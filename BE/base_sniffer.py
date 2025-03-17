import threading
import logging
import numpy as np
import time
from collections import OrderedDict, defaultdict, deque
from classification import Classification
from config import MONITORING_IP_LIST, MONITORING_PERIOD, TARGET_APPLICATIONS
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class BaseSniffer:
    def __init__(self, socketio, interface="en0", bitmap_path="bitmap_record.pkl"):
        """
        패킷 스니핑을 위한 기본 클래스
        """
        self.interface = interface
        self.sessions = OrderedDict()
        self.lock = threading.Lock()  # 동기화 객체 추가
        self.classification = Classification(bitmap_path)
        self.predicted = []
        self.monitoring_ips = MONITORING_IP_LIST
        self.traffic_tmp = defaultdict(lambda: defaultdict(list))
        self.traffic_rate_detail = {src_ip: defaultdict(deque) for src_ip in self.monitoring_ips}
        self.traffic_rate_total = {src_ip: deque() for src_ip in self.monitoring_ips}
        self.socketio = socketio

        self.TP = defaultdict(list)
        self.FP = defaultdict(list)
        self.FN = []

    def get_packet_direction(self, src_ip, dst_ip):
        """
        패킷의 방향을 결정하는 함수
        """
        if src_ip in self.monitoring_ips:
                direction = "outbound"
        elif dst_ip in self.monitoring_ips:
            direction = "inbound"
        else:
            return None
        return direction
    
    def handle_tls(self, packet, session_key):
        """
        TLS 핸드셰이크 정보를 감지하여 세션에 저장 (Pyshark만 적용 가능)
        """
        pass  # PysharkSniffer에서만 구현

    def process_packet(self, packet):
        """
        패킷을 처리하는 함수 (자식 클래스에서 구현 필요)
        """
        raise NotImplementedError("process_packet()은 자식 클래스에서 구현해야 합니다.")

    def log_session_info(self, session_key, score, predict):
        """
        세션 정보를 로깅하는 함수
        """
        logging.info(f"세션: {session_key} 예측: {predict} 점수: {score} SNI: {self.sessions.get(session_key, {}).get('sni', 'None')}")

    def start_sniffing(self):
        """
        패킷 스니핑을 시작하는 함수 (자식 클래스에서 구현 필요)
        """
        raise NotImplementedError("start_sniffing()은 자식 클래스에서 구현해야 합니다.")
    
    def add_traffic(self, src_ip, dst_ip, packet_size):
        """
        트래픽을 추가하는 함수
        """
        packet_size = abs(packet_size)
        self.traffic_tmp[src_ip][dst_ip].append(packet_size)
    
    def handle_packet(self, session_key, packet_size):
        """
        패킷 처리
        """
        with self.lock:
            session = self.sessions.setdefault(session_key, {'sni': None, 'data': deque(maxlen=self.classification.VEC_LEN)})
            
            self.add_traffic(session_key[0], session_key[2], packet_size)
            if session_key in self.predicted:
                return
            session['data'].append(packet_size)

            if len(session['data']) == self.classification.VEC_LEN:
                prediction_thread = threading.Thread(target=self.prediction, args=(session_key, session['data']))
                prediction_thread.start()
    
    def monitor_traffic(self):
        """
        트래픽 계산하는 함수
        """
        seconds_passed = 0
        while True:
            for src_ip in self.monitoring_ips: # 모니터링 대상 IP에 대해
                total_traffic = 0

                tmp_keys = set(self.traffic_tmp[src_ip].keys())
                rate_keys = set(self.traffic_rate_detail[src_ip].keys())

                for key in tmp_keys & rate_keys: # 교집합
                    traffic_size = sum(self.traffic_tmp[src_ip][key])
                    total_traffic += traffic_size
                    self.traffic_rate_detail[src_ip][key].append(traffic_size)

                for key in rate_keys - tmp_keys: # rate_keys에만 있는 것 = 트래픽량이 0인것
                    self.traffic_rate_detail[src_ip][key].append(0)

                for key in tmp_keys - rate_keys: # tmp_keys에만 있는 것 = 새로운 트래픽
                    self.traffic_rate_detail[src_ip][key].extend([0] * min(seconds_passed, MONITORING_PERIOD))
                    traffic_size = sum(self.traffic_tmp[src_ip][key])
                    total_traffic += traffic_size
                    self.traffic_rate_detail[src_ip][key].append(traffic_size)
                
                self.traffic_rate_total[src_ip].append(total_traffic)
                
                if seconds_passed >= MONITORING_PERIOD:
                    self.traffic_rate_total[src_ip].popleft()
                    for dst_ip in self.traffic_rate_detail[src_ip].keys():
                        self.traffic_rate_detail[src_ip][dst_ip].popleft()

            self.traffic_tmp.clear()
            seconds_passed += 1
            formatted_traffic = {src_ip: list(value) for src_ip, value in self.traffic_rate_total.items()}
            self.emit("traffic_total",{
                "seconds_passed": seconds_passed,
                "traffic_total": formatted_traffic})
            time.sleep(1) # 1초마다 트래픽 계산

    def emit(self, message, data):
        """
        트래픽 전송하는 함수
        """
        self.socketio.emit(message, data)
    
    def prediction(self, session_key, data):
        """
        세션 예측 함수
        """
        score, predict, score_dict = self.classification.predict(session_key, np.array(data, dtype=np.int16))
        sni = self.sessions.get(session_key, {}).get('sni', 'None')
        logging.info(f"세션: {session_key} SNI: {sni} 예측: {predict} 점수: {score}\n상세점수: {score_dict}")
        self.predicted.append(session_key)

        self.socketio.emit("streaming_detection", {
            'ip': session_key[0],
            'services': [predict],
        })

        if sni is not None:
            matched = False

            for app_sni in TARGET_APPLICATIONS.keys():
                if app_sni in sni:
                    real_app = TARGET_APPLICATIONS[app_sni]
                    matched = True
                    if predict == real_app:
                        self.TP[real_app].append(score)
                        #logging.info(f"예측 성공: {real_app} 점수: {score} 상세 점수: {score_dict}")
                    else:
                        self.FP[real_app].append(score)
                        #logging.info(f"예측 실패: {real_app} 점수: {score} 상세 점수: {score_dict}")
                    break
            
            if not matched:
                self.FN.append(score)
                #logging.info(f"실제 앱 미정: {sni} 예측: {predict} 점수: {score} 상세 점수: {score_dict}")
        
    def visualization(self, log_path):
        """
        시각화 함수
        """
        with self.lock:
            plt.figure(figsize=(12, 6))
            for app_name in self.TP.keys():
                tp_scores = self.TP[app_name]
                plt.hist(tp_scores, bins=20, alpha=0.5, label=f'{app_name} TP', cumulative=True)
            for app_name in self.FP.keys():
                fp_scores = self.FP[app_name]
                plt.hist(fp_scores, bins=20, alpha=0.5, label=f'{app_name} FP', cumulative=True)
            plt.hist(self.FN, bins=20, alpha=0.5, color='g', label='FN', cumulative=True)
            plt.legend(loc='upper right')
            plt.title('Prediction Result')
            plt.xlabel('Score')
            plt.ylabel('Count')
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            log_path = Path(log_path)
            log_path.mkdir(parents=True, exist_ok=True)

            # 중복 방지를 위해 result_숫자.png 추가
            i = 1
            if (log_path / f"result_{timestamp}.png").exists():
                while (log_path / f"result_{timestamp}_{i}.png").exists():
                    i += 1
                save_path = log_path / f"result_{timestamp}_{i}.png"
            else:
                save_path = log_path / f"result_{timestamp}.png"

            # 📌 그래프 저장
            plt.savefig(save_path)
            plt.close()

            logging.info(f"시각화 결과 저장: {save_path}")

            # 데이터 초기화
            self.TP.clear()
            self.FP.clear()
            self.FN.clear()
