import pyshark
import logging
import threading
import numpy as np
import asyncio
import argparse
from collections import deque
from base_sniffer import BaseSniffer

class PysharkSniffer(BaseSniffer):
    def __init__(self, socketio, app, interface="en0", bitmap_path="bitmap_record.pkl"):
        super().__init__(socketio, app, interface, bitmap_path)

    def handle_tls(self, packet, session_key):
        """
        TLS SNI 정보를 감지하여 저장
        """
        if hasattr(packet, "tls"):
            if hasattr(packet.tls, "handshake_extensions_server_name"):
                session = self.sessions.setdefault(session_key, {'sni': None, 'data': deque(maxlen=self.classification.VEC_LEN)})
                session['sni'] = packet.tls.handshake_extensions_server_name

    def get_tcp_info(self, packet):
        """
        TCP 패킷 정보 반환
        """
        src_port = packet.tcp.srcport
        dst_port = packet.tcp.dstport
        packet_size = int(packet.ip.len) - int(packet.ip.hdr_len) - int(packet.tcp.hdr_len)
        return src_port, dst_port, packet_size, 6
    
    def get_udp_info(self, packet):
        """
        UDP 패킷 정보 반환
        """
        src_port = packet.udp.srcport
        dst_port = packet.udp.dstport
        packet_size = int(packet.ip.len) - int(packet.ip.hdr_len) - 8
        return src_port, dst_port, packet_size, 17
    
    def process_packet(self, packet):
        """
        Pyshark에서 캡처한 패킷을 처리
        """
        try:
            if not hasattr(packet, "ip"):
                return
            
            src_ip = packet.ip.src
            dst_ip = packet.ip.dst

            direction = self.get_packet_direction(src_ip, dst_ip)
            if direction is None:
                return

            if hasattr(packet, "tcp"):
                src_port, dst_port, packet_size, protocol = self.get_tcp_info(packet)
            elif hasattr(packet, "udp"):
                src_port, dst_port, packet_size, protocol = self.get_udp_info(packet)
            else:
                return
            
            if packet_size == 0:
                return

            if direction == 'inbound':
                src_ip, dst_ip = dst_ip, src_ip
                src_port, dst_port = dst_port, src_port
            else:
                packet_size = -packet_size
            session_key = (src_ip, src_port, dst_ip, dst_port, protocol)

            self.handle_tls(packet, session_key)
            self.handle_packet(session_key, packet_size)

        except Exception as e:
            logging.error(f"[ERROR!] {e}")

    def start_sniffing(self):
        """
        Pyshark를 이용하여 패킷 스니핑 실행
        """
        logging.info(f"Pyshark Sniffing 시작: 인터페이스 {self.interface}")

        def sniff_packets():
            try:
                asyncio.set_event_loop(asyncio.new_event_loop())
                capture = pyshark.LiveCapture(interface=self.interface)
                for packet in capture.sniff_continuously():
                    self.process_packet(packet)
            except Exception as e:
                logging.error(f"[ERROR] 패킷 스니핑 중 오류 발생: {e}")

        sniffing_thread = threading.Thread(target=sniff_packets, daemon=True)
        sniffing_thread.start()
    
    def handle_pcap(self, pcap):
        """
        Pyshark를 이용하여 pcap 파일 처리
        """
        logging.info(f"Pyshark로 pcap 파일 처리: {pcap}")
        try:
            cap = pyshark.FileCapture(pcap)
            for packet in cap:
                self.process_packet(packet)
        except Exception as e:
            logging.error(f"[ERROR] pcap 파일 처리 중 오류 발생: {e}")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-f", "--file", help="pcap 파일 경로")

    args = parser.parse_args()
    if args.file:
        logging.basicConfig(level=logging.INFO)
        sniffer = PysharkSniffer(None)
        sniffer.handle_pcap(args.file)
        sniffer.visualization("../logs")
    else:
        print("pcap 파일 경로를 입력해주세요.")