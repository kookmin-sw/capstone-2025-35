import pickle
import numpy as np
from bitarray import bitarray
from config import DISC_RANGE

class Classification:
    def __init__(self, file_path = 'bitmap_record.pkl'):
        """
        분류기 초기화
        Args:
            file_path (str): 비트맵 파일 경로
        """
        with open(file_path, 'rb') as f:
            self.bitmapPKL = pickle.load(f)
        self.CLASSES = self.bitmapPKL['class']
        self.N_CLASSES = len(self.CLASSES)
        self.BITMAP = {
            "total": self.bitmapPKL['bitmap'][0],
            "inbound": self.bitmapPKL['bitmap'][1],
            "outbound": self.bitmapPKL['bitmap'][2]
        }
        self.N_GRAM = self.bitmapPKL['N_GRAM']
        self.VEC_LEN = self.bitmapPKL['VEC_LEN']
        self.disc = self.bitmapPKL['disc']
    
    def discretize_values(self, value, disc_range):
        """
        값을 이산화하는 함수
        Args:
            value (int): 이산화할 값
            disc_range (list): 이산화 구간
        Returns:
            int: 이산화된 값
        """
        if value == 0:
            return DISC_RANGE
        return np.searchsorted(disc_range, value, side='right') - 1 + (1 if value > 0 else 0)
    
    def embedding_packet(self, packet_seq):
        """
        패킷 데이터를 비트맵으로 변환하는 함수
        Args:
            packet_seq (list): 패킷 시퀀스
        Returns:
            bitarray: 패킷 비트맵
        """
        dr = len(self.disc)
        L = dr ** self.N_GRAM
        res = bitarray(L)
        res.setall(0)  # 초기화

        discretized_data = [self.discretize_values(val, self.disc) for val in packet_seq]

        for idx in range(0, min(len(discretized_data), self.VEC_LEN) - self.N_GRAM + 1):
            n_gram = discretized_data[idx:idx + self.N_GRAM]
            pos = sum((dr ** i) * val for i, val in enumerate(reversed(n_gram)))
            res[pos] = 1

        return res
    
    def predict(self, session_key, packet_total):
        """
        패킷 데이터를 분류하는 함수
        Args:
            session_key (str): 세션 키
            packet_total (np.array): 패킷 시퀀스
        Returns:
            tuple: 점수 및 예측 결과
        """
        packet_total = packet_total[:self.VEC_LEN]
        packet_inbound = packet_total[packet_total > 0]
        packet_outbound = packet_total[packet_total < 0]
        
        total_bitmap = self.embedding_packet(packet_total)
        inbound_bitmap = self.embedding_packet(packet_inbound)
        outbound_bitmap = self.embedding_packet(packet_outbound)
        scores = np.zeros(self.N_CLASSES)  # 점수 배열 초기화

        for idx in range(self.N_CLASSES):
            scores[idx] = ((total_bitmap & self.BITMAP['total'][idx]).count(1) + 
                           (inbound_bitmap & self.BITMAP['inbound'][idx]).count(1) + 
                           (outbound_bitmap & self.BITMAP['outbound'][idx]).count(1))
        score = np.max(scores)
        
        return score, self.CLASSES[np.argmax(scores)]