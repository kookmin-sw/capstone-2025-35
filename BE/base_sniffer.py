import threading
import logging
import numpy as np
import time
from collections import OrderedDict, defaultdict, deque
from classification import Classification
from config import MONITORING_IP_LIST, MONITORING_PERIOD

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