import pyshark
import logging
import threading
import numpy as np
import asyncio
from base_sniffer import BaseSniffer

class PysharkSniffer(BaseSniffer):
    def __init__(self, socketio, interface="en0", bitmap_path="bitmap_record.pkl"):
        super().__init__(socketio, interface, bitmap_path)

    def handle_tls(self, packet, session_key):
        """
        TLS SNI 정보를 감지하여 저장
        """
        if hasattr(packet, "tls") and hasattr(packet.tls, "handshake_extensions_server_name"):
            self.sessions[session_key]['sni'] = packet.tls.handshake_extensions_server_name

    def process_packet(self, packet):
        """
        Pyshark에서 캡처한 패킷을 처리
        """
        try:
            if not hasattr(packet, "ip"):
                return
            
            src_ip = packet.ip.src
            dst_ip = packet.ip.dst
            ip_len = int(packet.ip.len)
            ip_hdr_len = int(packet.ip.hdr_len)

            direction = self.get_packet_direction(src_ip, dst_ip)
            if direction is None:
                return

            if hasattr(packet, "tcp"):
                protocol = 6
                src_port = packet.tcp.srcport
                dst_port = packet.tcp.dstport
                tcp_hdr_len = int(packet.tcp.hdr_len)
                packet_size = ip_len - ip_hdr_len - tcp_hdr_len
            elif hasattr(packet, "udp"):
                protocol = 17
                src_port = packet.udp.srcport
                dst_port = packet.udp.dstport
                packet_size = ip_len - ip_hdr_len - 8
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

            with self.lock:
                if session_key not in self.sessions:
                    self.sessions[session_key] = {'sni': None, 'data': []}
                
                self.add_traffic(src_ip, dst_ip, packet_size)
                self.handle_tls(packet, session_key)

                self.sessions[session_key]['data'].append(packet_size)

                if len(self.sessions[session_key]['data']) == self.classification.VEC_LEN:
                    self.prediction(session_key, self.sessions[session_key]['data'])

        except Exception as e:
            logging.error(f"[ERROR] {e}")

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