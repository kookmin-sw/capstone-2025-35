import pyshark
from collections import defaultdict, OrderedDict
from classification import Classification
import numpy as np
import logging
import threading

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class PysharkSniffer:
    def __init__(self, interface="en0", bitmap_path="bitmap_record.pkl"):
        self.interface = interface
        self.sessions = OrderedDict()
        self.initial_ips = {}
        self.lock = threading.Lock()  # 동기화 객체 추가
        self.classification = Classification(bitmap_path)

    def get_session_key(self, src_ip, src_port, dst_ip, dst_port, protocol):
        """
        세션 키를 생성하는 함수 (원자성을 유지하도록 별도로 분리)
        """
        try:
            return '_'.join([str(src_ip), str(src_port), str(dst_ip), str(dst_port), str(protocol)])
        except TypeError:
            return '_'.join([str(src_ip), "0", str(dst_ip), "0", str(protocol)])

    def get_packet_direction(self, src_ip, dst_ip):
        """
        패킷의 방향을 결정하는 함수
        """
        ip1, ip2 = self.initial_ips.get(src_ip, (src_ip, dst_ip))
        return "-" if src_ip == ip1 else "+"

    def handle_tls(self, packet, session_key):
        """
        TLS 핸드셰이크 정보를 감지하여 세션에 저장
        """
        if hasattr(packet, "tls") and hasattr(packet.tls, "handshake_extensions_server_name"):
            self.sessions[session_key]['sni'] = packet.tls.handshake_extensions_server_name

    def process_packet(self, packet):
        """
        패킷을 처리하는 함수 (개선된 원자성 유지)
        """
        try:
            if not hasattr(packet, "ip"):
                return
            
            # 기본 정보 추출
            src_ip = packet.ip.src
            dst_ip = packet.ip.dst
            ip_total_length = int(packet.ip.len)
            ip_header_length = int(packet.ip.hdr_len)

            if hasattr(packet, "tcp"):
                src_port = packet.tcp.srcport
                dst_port = packet.tcp.dstport
                protocol = 6
                tcp_header_length = int(packet.tcp.hdr_len)
                packet_size = ip_total_length - ip_header_length - tcp_header_length
            elif hasattr(packet, "udp"):
                src_port = packet.udp.srcport
                dst_port = packet.udp.dstport
                protocol = 17
                packet_size = ip_total_length - ip_header_length - 8
            else:
                return

            # 세션 키 설정
            session_key = self.get_session_key(src_ip, src_port, dst_ip, dst_port, protocol)
            reversed_key = self.get_session_key(dst_ip, dst_port, src_ip, src_port, protocol)

            # 원자적으로 세션 갱신
            with self.lock:
                if session_key in self.sessions:
                    pass
                elif reversed_key in self.sessions:
                    session_key = reversed_key
                else:
                    self.initial_ips[session_key] = (src_ip, dst_ip)
                    self.sessions[session_key] = {'sni': None, 'data': []}

                # TLS 처리
                self.handle_tls(packet, session_key)

                # 패킷 방향 감지 및 추가
                direction = self.get_packet_direction(src_ip, dst_ip)
                if 0 <= packet_size <= 1600:
                    packet_size = -packet_size if direction == "-" else packet_size
                    self.sessions[session_key]['data'].append(packet_size)

                # 세션 데이터가 VEC_LEN을 넘으면 판별
                if len(self.sessions[session_key]['data']) == 20:
                    score, predict = self.classification.predict(session_key, np.array(self.sessions[session_key]['data'], dtype=np.int16))
                    logging.info(f"세션: {session_key} 예측: {predict} 점수: {score}")
                    
        except Exception as e:
            logging.error(f"[ERROR] {e}")

    def start_sniffing(self):
        """
        패킷 스니핑을 시작하는 함수
        """
        logging.info(f"패킷 스니핑 시작: 인터페이스 {self.interface}")
        
        def sniff_packets():
            try:
                capture = pyshark.LiveCapture(interface=self.interface)
                for packet in capture.sniff_continuously():
                    self.process_packet(packet)
            except Exception as e:
                logging.error(f"[ERROR] 패킷 스니핑 중 오류 발생: {e}")

        # 백그라운드 스레드에서 실행
        sniffing_thread = threading.Thread(target=sniff_packets, daemon=True)
        sniffing_thread.start()

if __name__ == "__main__":
    sniffer = PysharkSniffer()
    sniffer.start_sniffing()
    input("Press Enter to stop sniffing...\n")