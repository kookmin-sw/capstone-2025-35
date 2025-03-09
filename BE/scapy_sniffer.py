import logging
import numpy as np
from scapy.all import sniff, IP, TCP, UDP
from base_sniffer import BaseSniffer

class ScapySniffer(BaseSniffer):
    def __init__(self, interface="en0", bitmap_path="bitmap_record.pkl"):
        super().__init__(interface, bitmap_path)

    def process_packet(self, packet):
        """
        Scapy에서 캡처한 패킷을 처리
        """
        try:
            if not packet.haslayer(IP):
                return

            src_ip = packet[IP].src
            dst_ip = packet[IP].dst

            if packet.haslayer(TCP):
                protocol = 6
                src_port = packet[TCP].sport
                dst_port = packet[TCP].dport
                packet_size = len(bytes(packet["TCP"].payload))
            elif packet.haslayer(UDP):
                protocol = 17
                src_port = packet[UDP].sport
                dst_port = packet[UDP].dport
                packet_size = len(bytes(packet["UDP"].payload))
            else:
                return
            
            direction = self.get_packet_direction(src_ip, dst_ip)
            if direction is None:
                return
            
            if direction == 'inbound':
                src_ip, dst_ip = dst_ip, src_ip
                src_port, dst_port = dst_port, src_port
            else:
                packet_size = -packet_size

            session_key = (src_ip, src_port, dst_ip, dst_port, protocol)

            with self.lock:
                if session_key not in self.sessions:
                    self.sessions[session_key] = {'sni': None, 'data': []}

                self.sessions[session_key]['data'].append(packet_size)

                if len(self.sessions[session_key]['data']) == 20:
                    score, predict = self.classification.predict(session_key, np.array(self.sessions[session_key]['data'], dtype=np.int16))
                    self.log_session_info(session_key, score, predict)
                    self.predicted.append(session_key)

        except Exception as e:
            logging.error(f"[ERROR] {e}")

    def start_sniffing(self):
        """
        Scapy를 이용하여 패킷 스니핑 실행
        """
        logging.info(f"Scapy Sniffing 시작: 인터페이스 {self.interface}")
        sniff(iface=self.interface, prn=self.process_packet, store=False)