import logging
import numpy as np
from scapy.all import sniff, IP, TCP, UDP
from base_sniffer import BaseSniffer

class ScapySniffer(BaseSniffer):
    def __init__(self, socketio, interface="en0", bitmap_path="bitmap_record.pkl"):
        super().__init__(socketio, interface, bitmap_path)

    def get_tcp_info(self, packet):
        """
        TCP 패킷 정보 반환
        """
        src_port = packet[TCP].sport
        dst_port = packet[TCP].dport
        packet_size = len(bytes(packet["TCP"].payload))
        return src_port, dst_port, packet_size, 6
    
    def get_udp_info(self, packet):
        """
        UDP 패킷 정보 반환
        """
        src_port = packet[UDP].sport
        dst_port = packet[UDP].dport
        packet_size = len(bytes(packet["UDP"].payload))
        return src_port, dst_port, packet_size, 17

    def process_packet(self, packet):
        """
        Scapy에서 캡처한 패킷을 처리
        """
        try:
            if not packet.haslayer(IP):
                return

            src_ip = packet[IP].src
            dst_ip = packet[IP].dst

            direction = self.get_packet_direction(src_ip, dst_ip)
            if direction is None:
                return

            if packet.haslayer(TCP):
                src_port, dst_port, packet_size, protocol = self.get_tcp_info(packet)
            elif packet.haslayer(UDP):
                src_port, dst_port, packet_size, protocol = self.get_udp_info(packet)
            else:
                return
            
            if direction == 'inbound':
                src_ip, dst_ip = dst_ip, src_ip
                src_port, dst_port = dst_port, src_port
            else:
                packet_size = -packet_size

            session_key = (src_ip, src_port, dst_ip, dst_port, protocol)

            self.handle_packet(session_key, packet_size)

        except Exception as e:
            logging.error(f"[ERROR] {e}")

    def start_sniffing(self):
        """
        Scapy를 이용하여 패킷 스니핑 실행
        """
        logging.info(f"Scapy Sniffing 시작: 인터페이스 {self.interface}")
        sniff(iface=self.interface, prn=self.process_packet, store=False)