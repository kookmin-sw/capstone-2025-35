#%%
import pandas as pd
import numpy as np
from pathlib import Path
import ast
from sklearn.feature_extraction.text import TfidfVectorizer
#%%
TARGET_SNI = {
    "youtube": ["googlevideo.com"],
    "youtube_tls": ["googlevideo.com"],
    "instagram": ["fbcdn.net"],
    "instagram_tls": ["fbcdn.net"],
    "netflix": ["nflxvideo.net"],
    "navertv": ["naver-vod.pstatic.net", "smartmediarep.com"],
    "wavve": ["vod.cdn.wavve.com"],
    "soop": ["stream.sooplive.co.kr"],
    "steam": ["steambroadcast.akamaized.net"],
    "coupangplay": ["cosmos.coupangstreaming.com"],
}
FIRST_N_PKTS = 100
VEC_LEN = 4
DISC_RANGE = 13
N_GRAM = 4
#%%>e
class Classification:
    def __init__(self, csv_files, flow_seq):
        self.csv_files = csv_files
        self.flow_seq = flow_seq
        self.flow_seq['Dummy'] = {'total': []}
        self.disc = None

    def forward(self):
        self.load_csv()
        self.get_in_n_out()
        self.compute_discrete()
        self.discrete_flow()
        self.embedding_flow()
    
    def load_csv(self):
        for csv_file in self.csv_files:
            self.handle_csv(csv_file)

    def handle_csv(self, csv_file):
        parts = csv_file.parts
        app_name = parts[-4]
        if app_name not in TARGET_SNI:
            return
        df = pd.read_csv(csv_file)
        self.classify_dummy(df, app_name)
    
    def classify_dummy(self, df, app_name):
        target_sni = TARGET_SNI[app_name]
        app_df = df[df['SNI'].apply(lambda sni: any(target in sni for target in target_sni if isinstance(sni, str)))]
        dummy_df = df[~df['SNI'].apply(lambda sni: any(target in sni for target in target_sni if isinstance(sni, str)))]

        app_seq = app_df['SPLT-Data'].tolist()
        self.flow_seq[app_name]['total'].extend(app_seq)

        dummy_seq = dummy_df['SPLT-Data'].tolist()
        self.flow_seq['Dummy']['total'].extend(dummy_seq)
    
    def get_in_n_out(self):
        for app_name, data in self.flow_seq.items():
            total_seq = []
            in_seq = []
            out_seq = []

            for seq in data['total']:
                if isinstance(seq, str):
                    seq = ast.literal_eval(seq)  # 문자열 -> 리스트로 변환
                int_seq = np.array([int(s) for s in seq][:FIRST_N_PKTS], dtype=np.int32)
                total_seq.append(int_seq)
                in_seq.append(int_seq[int_seq > 0])
                out_seq.append(int_seq[int_seq < 0])
            
            self.flow_seq[app_name]['in'] = in_seq
            self.flow_seq[app_name]['out'] = out_seq
            self.flow_seq[app_name]['total'] = total_seq
    
    def compute_discrete(self):
        total_seq = []
        for x, data in self.flow_seq.items():
            total_seq.extend(data['total'])
        
        total_seq = np.hstack(total_seq)
        neg_l, neg_disc_range = pd.qcut(total_seq[total_seq < 0], q=DISC_RANGE-1, retbins=True, labels=False, duplicates='drop')
        pos_l, pos_disc_range = pd.qcut(total_seq[total_seq > 0], q=DISC_RANGE-1, retbins=True, labels=False, duplicates='drop')
        disc_range = np.hstack([[-np.inf], neg_disc_range, [0], pos_disc_range, [np.inf]])
        self.disc = disc_range
    
    def discrete_flow(self):
        for app_name, data in self.flow_seq.items():
            total_seq = data['total']
            in_seq = data['in']
            out_seq = data['out']

            total_seq = [[int((np.searchsorted(self.disc, value, side='right') - 1) + (1 if value > 0 else 0)) for value in seq] for seq in total_seq]
            in_seq = [[int((np.searchsorted(self.disc, value, side='right') - 1) + (1 if value > 0 else 0)) for value in seq] for seq in in_seq]
            out_seq = [[int((np.searchsorted(self.disc, value, side='right') - 1) + (1 if value > 0 else 0)) for value in seq] for seq in out_seq]

            self.flow_seq[app_name]['disc_total'] = total_seq
            self.flow_seq[app_name]['disc_in'] = in_seq
            self.flow_seq[app_name]['disc_out'] = out_seq

    def embedding_flow(self):
        for app_name, data in self.flow_seq.items():
            total_seq = data['disc_total']
            in_seq = data['disc_in']
            out_seq = data['disc_out']

            total_seq = [self.embedding_packets(seq) for seq in total_seq]
            in_seq = [self.embedding_packets(seq) for seq in in_seq]
            out_seq = [self.embedding_packets(seq) for seq in out_seq]

            self.flow_seq[app_name]['embedding_seq_total'] = total_seq
            self.flow_seq[app_name]['embedding_seq_in'] = in_seq
            self.flow_seq[app_name]['embedding_seq_out'] = out_seq

            total_ = [val for seq in total_seq for val in self.embedding_packets(seq)]
            in_ = [val for seq in in_seq for val in self.embedding_packets(seq)]
            out_ = [val for seq in out_seq for val in self.embedding_packets(seq)]

            self.flow_seq[app_name]['embedding_total'] = total_
            self.flow_seq[app_name]['embedding_in'] = in_
            self.flow_seq[app_name]['embedding_out'] = out_
    
    def embedding_packets(self, packet_seq):
        dr = len(self.disc)

        embedding_data = []
        for i in range(0, len(packet_seq) - N_GRAM + 1):
            n_gram = packet_seq[i:i + N_GRAM]
            embedded = sum((dr ** j) * val for j, val in enumerate(reversed(n_gram)))
            embedding_data.append(embedded)
        
        return embedding_data
    
    def compute_tfidf(self):
        documents = []
        labels = []

        for app_name, data in self.flow_seq.items():
            if 'embedding_total' in data:
                # 각 앱의 임베딩 리스트를 문자열로 변환
                doc = ' '.join(map(str, data['embedding_total']))
                documents.append(doc)
                labels.append(app_name)  # 나중에 어떤 앱에 해당하는 문서인지 알기 위해 저장

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(documents)

        # 저장
        self.tfidf_matrix = tfidf_matrix
        self.tfidf_feature_names = vectorizer.get_feature_names_out()
        self.tfidf_labels = labels  # 앱 이름과 매칭
        
        
#%%
if __name__ == '__main__':
    csv_folder = Path('/Users/minsuhong/Library/CloudStorage/GoogleDrive-alstnghd77@gmail.com/내 드라이브/CAPSTONE/csv')
    csv_files = list(csv_folder.glob('**/*.csv'))
    flow_seq = {f.name:{'total':[]} for f in csv_folder.iterdir() if f.is_dir()}
    cls = Classification(csv_files, flow_seq)
# %%
    cls.forward()
# %%
    cls.flow_seq['coupangplay']['disc_total']
# %%
    cls.compute_tfidf()
# %%
    cls.tfidf_matrix
# %%
target = 'youtube'
index = cls.tfidf_labels.index(target)
vector = cls.tfidf_matrix[index].toarray()[0]

# 단어와 TF-IDF 값 묶어서 보기
for word, score in zip(cls.tfidf_feature_names, vector):
    if score > 0:
        print(f"{word}: {score:.4f}")
# %%
