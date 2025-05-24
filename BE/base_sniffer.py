import threading
import logging
import numpy as np
import time
from collections import OrderedDict, defaultdict, deque
from classification import Classification
from config import MONITORING_IP_LIST, MONITORING_PERIOD, TARGET_APPLICATIONS
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import matplotlib.pyplot as plt
from DB.utils import insert_packet_log
from flask import current_app

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class BaseSniffer:
    def __init__(self, socketio, app, interface="en0", bitmap_path="bitmap_record.pkl"):
        """
        패킷 스니핑을 위한 기본 클래스
        """
        self.app = app
        self.interface = interface
        self.sessions = OrderedDict()
        self.lock = threading.Lock()  # 동기화 객체 추가
        self.classification = Classification(bitmap_path)
        self.predicted = []
        self.detected_sessions = [] # 새 코드
        self.monitoring_ips = MONITORING_IP_LIST
        self.traffic_tmp = defaultdict(lambda: {'outbound': defaultdict(list), 'inbound': defaultdict(list)})
        self.traffic_rate_detail = {
            src_ip: {
                'outbound': defaultdict(deque),
                'inbound': defaultdict(deque)
            } for src_ip in self.monitoring_ips
        }
        self.traffic_rate_total = {
            src_ip: {
                'outbound': deque(),
                'inbound': deque()
            } for src_ip in self.monitoring_ips
        }
        self.socketio = socketio
        self.protocol_stats = defaultdict(lambda: {'tcp': 0, 'udp': 0, 'icmp': 0, 'other': 0})
        self.port_stats = defaultdict(lambda: defaultdict(int))
        self.TP = defaultdict(list)
        self.FP = defaultdict(list)
        self.TN = []
        self.predict_app = defaultdict(list)

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

    def get_tcp_info(self, packet):
        """
        TCP 패킷 정보 반환 (자식 클래스에서 구현 필요)
        """
        raise NotImplementedError("get_tcp_info()은 자식 클래스에서 구현해야 합니다.")
    
    def get_udp_info(self, packet):
        """
        UDP 패킷 정보 반환 (자식 클래스에서 구현 필요)
        """
        raise NotImplementedError("get_udp_info()은 자식 클래스에서 구현해야 합니다.")

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
    

    def send_detected_sessions(self):
        # detected_sessions 리스트를 그대로 보내기  서버 요청
        # print(f"[INFO] base_sniffer.py -> send_detected_sessions 호출")
        self.socketio.emit('detected_sessions_update', {'sessions': self.detected_sessions})
        # print(f"[INFO] base_sniffer.py -> send_detected_sessions 전송")
        # print(f"[INFO] base_sniffer.py -> send_detected_sessions 에서 detected_sessions: {self.detected_sessions}")
    
    def add_traffic(self, src_ip, dst_ip, packet_size):
        """
        송수신 방향에 따라 트래픽을 저장하는 함수
        """
        if packet_size <= 0:
            direction = 'outbound'
        else:
            direction = 'inbound'
        if direction is None:
            return
        packet_size = abs(packet_size)
        self.traffic_tmp[src_ip][direction][dst_ip].append(packet_size)
    
    def handle_packet(self, session_key, packet_size):
        """
        패킷 처리
        """
        with self.lock:
            src_ip, src_port, dst_ip, dst_port, protocol = session_key
            session = self.sessions.setdefault(session_key, {'sni': None, 'data': deque(maxlen=self.classification.VEC_LEN)})
            
            if protocol == 6:
                self.protocol_stats[src_ip]['tcp'] += 1
            elif protocol == 17:
                self.protocol_stats[src_ip]['udp'] += 1
            elif protocol == 1:
                self.protocol_stats[src_ip]['icmp'] += 1
            else:
                self.protocol_stats[src_ip]['other'] += 1

            self.port_stats[src_ip][src_port] += 1
            self.add_traffic(session_key[0], session_key[2], packet_size)
            if session_key in self.predicted:
                return
            
            if len(session['data']) < self.classification.VEC_LEN:
                session['data'].append(packet_size)

            if len(session['data']) == self.classification.VEC_LEN:
                if protocol == 6 and list(session['data'])[:3] != [0, 0, 0]:
                    return
                prediction_thread = threading.Thread(target=self.prediction, args=(session_key, session['data']))
                prediction_thread.start()
    
    def monitor_traffic(self):
        """
        트래픽 계산하는 함수
        """
        seconds_passed = 0
        while True:
            for src_ip in self.monitoring_ips:
                for direction in ['outbound', 'inbound']:
                    total_traffic = 0
                    tmp_keys = set(self.traffic_tmp[src_ip][direction].keys())
                    rate_keys = set(self.traffic_rate_detail[src_ip][direction].keys())
                    for key in tmp_keys & rate_keys:
                        traffic_size = sum(self.traffic_tmp[src_ip][direction][key])
                        total_traffic += traffic_size
                        self.traffic_rate_detail[src_ip][direction][key].append(traffic_size)

                    for key in rate_keys - tmp_keys:
                        self.traffic_rate_detail[src_ip][direction][key].append(0)

                    for key in tmp_keys - rate_keys:
                        self.traffic_rate_detail[src_ip][direction][key].extend([0] * min(seconds_passed, MONITORING_PERIOD))
                        traffic_size = sum(self.traffic_tmp[src_ip][direction][key])
                        total_traffic += traffic_size
                        self.traffic_rate_detail[src_ip][direction][key].append(traffic_size)

                    self.traffic_rate_total[src_ip][direction].append(total_traffic)

                    if seconds_passed >= MONITORING_PERIOD:
                        self.traffic_rate_total[src_ip][direction].popleft()
                        for dst_ip in self.traffic_rate_detail[src_ip][direction].keys():
                            self.traffic_rate_detail[src_ip][direction][dst_ip].popleft()

            self.traffic_tmp.clear()
            seconds_passed += 1
            formatted_traffic = {}
            for src_ip, data in self.traffic_rate_total.items():
                outbound = data['outbound'][-1] if data['outbound'] else 0
                inbound = data['inbound'][-1] if data['inbound'] else 0
                total = outbound + inbound
                formatted_traffic[src_ip] = total
            self.emit("traffic_total", {
                "seconds_passed": seconds_passed,
                "traffic_total": formatted_traffic
            })
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
        score, predict, score_dict = self.classification.predict(np.array(data, dtype=np.int16))
        sni = self.sessions.get(session_key, {}).get('sni', 'None')
        self.predicted.append(session_key)

        logging.info(f"세션: {session_key} 예측: {predict} 점수: {score} 상세 점수: {score_dict}")

        if score >= 25:

            self.emit("streaming_detection", {
                'ip': session_key[0],
                'services': [predict],
            })
            self.predict_app[session_key[0]].append(predict)
            src_ip, src_port, dst_ip, dst_port, protocol = session_key
            logging.info(f"[스트리밍 탐지] {src_ip}:{src_port} → {dst_ip}:{dst_port} ({protocol}) "
                        f"서비스: {predict}, 점수: {score}")
            
            # 세션 저장 (옵션)
            self.detected_sessions = [] #리스트 초기화
            self.detected_sessions.append({
                'src_ip': src_ip,
                'src_port': src_port,
                'dst_ip': dst_ip,
                'dst_port': dst_port,
                'protocol': protocol,
                'predict': predict,
                'score': score
            })
        
    def visualization(self, log_path):
        """
        시각화 함수
        """
        with self.lock:
            plt.figure(figsize=(12, 6))
            for app_name in self.TP.keys():
                tp_scores = self.TP[app_name]
                plt.hist(tp_scores, bins=20, alpha=0.5, label=f'{app_name} TP')
            for app_name in self.FP.keys():
                fp_scores = self.FP[app_name]
                plt.hist(fp_scores, bins=20, alpha=0.5, label=f'{app_name} FP')
            plt.hist(self.TN, bins=20, alpha=0.5, color='g', label='TN')
            plt.legend(loc='upper right')
            plt.title('Prediction Result')
            plt.xlabel('Collision')
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

            plt.savefig(save_path)
            plt.close()

            logging.info(f"시각화 결과 저장: {save_path}")

            # 데이터 초기화
            self.TP.clear()
            self.FP.clear()
            self.TN.clear()
    
    def traffic_detail(self, ip):
        """
        특정 IP의 트래픽 정보를 반환하는 함수
        """
        if ip not in self.monitoring_ips:
            return {"error": "해당 IP는 모니터링되지 않습니다."}

        inbound_values = self.traffic_rate_total[ip]['inbound']
        outbound_values = self.traffic_rate_total[ip]['outbound']

        total_inbound = sum(inbound_values) if inbound_values else 0
        total_outbound = sum(outbound_values) if outbound_values else 0
        total_traffic = total_inbound + total_outbound

        self.emit("traffic_detail", {
            "ip": ip,
            "download": total_inbound,
            "upload": total_outbound
        })

    def hostname(self, ip):
        """
        IP 주소에 대한 호스트 이름을 반환하는 함수
        """
        try:
            if ip == MONITORING_IP_LIST[0]:
                hostname = "localhost"
            else:
                hostname = ip
            self.emit("hostname_update", {
                "ip": ip,
                "hostname": hostname
            })
        except self.socket.herror:
            return None
    
    def protocol_stats_update(self, ip):
        """
        프로토콜 통계 업데이트 함수
        """
        if ip not in self.monitoring_ips:
            return {"error": "해당 IP는 모니터링되지 않습니다."}

        stats = self.protocol_stats[ip]
        self.emit("protocol_stats", {
            "ip": ip,
            "tcp": stats['tcp'],
            "udp": stats['udp'],
            "icmp": stats['icmp'],
            "other": stats['other']
        })

    def port_stats_update(self, ip):
        """
        포트 통계 업데이트 함수
        """
        if ip not in self.monitoring_ips:
            return {"error": "해당 IP는 모니터링되지 않습니다."}

        stats = self.port_stats[ip]
        self.emit("port_stats", {
            "ip": ip,
            "ports": dict(stats)
        })

    def packet_log_update(self, ip):
        """
        패킷 로그 업데이트 함수
        """
        if ip not in self.monitoring_ips:
            return {"error": "해당 IP는 모니터링되지 않습니다."}

        # 최신 세션 키들 중 해당 IP가 포함된 세션을 필터링
        relevant_sessions = [
            key for key in self.sessions.keys()
            if key[0] == ip or key[2] == ip
        ]

        for session_key in relevant_sessions:
            src_ip, src_port, dst_ip, dst_port, protocol = session_key
            data_list = self.sessions[session_key].get('data', [])

            inbound_size = sum(x for x in data_list if x > 0)
            outbound_size = sum(abs(x) for x in data_list if x < 0)

            utc_time = datetime.now(timezone.utc)
            timestamp = utc_time.astimezone(ZoneInfo("Asia/Seoul"))
            

            base_packet = {
                "time": int(time.time() * 1000),
                "source": src_ip,
                "destination": dst_ip,
                "protocol": {6: "TCP", 17: "UDP", 1: "ICMP"}.get(protocol, "OTHER"),
            }

            if inbound_size > 0:
                packet = base_packet.copy()
                packet.update({
                    "size": inbound_size,
                    "info": "DOWNLOAD"
                })
                self.emit("packet_log", {
                    "ip": ip,
                    "packet": packet
                })
                with self.app.app_context():
                    insert_packet_log(
                        timestamp=timestamp,
                        src_ip=src_ip,
                        src_port=src_port,
                        dst_ip=dst_ip,
                        dst_port=dst_port,
                        protocol=protocol,
                        size=inbound_size,
                        direction="DOWNLOAD"
                    )

            if outbound_size > 0:
                packet = base_packet.copy()
                packet.update({
                    "size": outbound_size,
                    "info": "UPLOAD"
                })
                self.emit("packet_log", {
                    "ip": ip,
                    "packet": packet
                })
                with self.app.app_context():
                    insert_packet_log(
                        timestamp=timestamp,
                        src_ip=src_ip,
                        src_port=src_port,
                        dst_ip=dst_ip,
                        dst_port=dst_port,
                        protocol=protocol,
                        size=outbound_size,
                        direction="UPLOAD"
                    )
    
    def streaming_detection_update(self, ip):
        if len(self.predict_app[ip]) > 0:
            self.emit("streaming_detection", {
                "ip": ip,
                "services": self.predict_app[ip]
            })

    def run_loop(self):
        """
        모니터링 대상 IP에 대해 주기적으로 packet_log_update 호출
        """
        while True:
            for ip in self.monitoring_ips:
                self.protocol_stats_update(ip)
                self.port_stats_update(ip)
                self.traffic_detail(ip)
                self.packet_log_update(ip)
            time.sleep(1)  # 매 1초마다 반복
