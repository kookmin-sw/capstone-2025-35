import threading
import logging
import numpy as np
from collections import OrderedDict
from classification import Classification
from config import MONITORING_IP_LIST

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class BaseSniffer:
    def __init__(self, interface="en0", bitmap_path="bitmap_record.pkl"):
        """
        패킷 스니핑을 위한 기본 클래스
        """
        self.interface = interface
        self.sessions = OrderedDict()
        self.lock = threading.Lock()  # 동기화 객체 추가
        self.classification = Classification(bitmap_path)
        self.predicted = []
        self.monitoring_ips = MONITORING_IP_LIST

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