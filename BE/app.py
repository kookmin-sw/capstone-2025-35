from flask import Flask, render_template
from flask_socketio import SocketIO
from scapy.all import sniff, IP
from collections import defaultdict
from dotenv import load_dotenv
from utils import get_mac_address, get_packet_direction, get_ports
import threading
import time
import os
import pickle

# 환경 변수 로드
load_dotenv()

# Flask 및 WebSocket 설정
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 모니터링 대상 설정
MONITORING_IP = os.getenv('MONITORING_IP', '192.168.1.1')
MONITORING_IP_SET = set(ip.strip() for ip in MONITORING_IP.split(','))
MONITORING_MAC_DICT = {}

# 설정 값
UPDATE_MAC_INTERVAL = 10  # MAC 주소 갱신 주기 (초)
MIN_PACKET_COUNT = 100  # 최소 패킷 개수 (탐지 기준)

# 패킷 데이터 저장소
packet_data = {
    "total": defaultdict(list),
    "inbound": defaultdict(list),
    "outbound": defaultdict(list),
}
app_detect_flag = set()

# 트래픽 데이터 저장소
traffic_data = {ip: 0 for ip in MONITORING_IP_SET}
prev_traffic_data = {ip: 0 for ip in MONITORING_IP_SET}
throughput_data = {ip: 0 for ip in MONITORING_IP_SET}

# Bitmap 데이터 로드
with open('bitmap_record.pkl', 'rb') as f:
    application_detect = pickle.load(f)

app_list = application_detect['class']
n_classes = len(app_list)
bitmap_data = {
    "total": application_detect['bitmap'][0],
    "inbound": application_detect['bitmap'][1],
    "outbound": application_detect['bitmap'][2],
}

# ======================== #
#       HELPER 함수        #
# ======================== #

def classify_packet(four_tuple):
    """
    패킷 데이터를 기반으로 애플리케이션을 식별하는 함수
    """
    if four_tuple in app_detect_flag:
        return  # 이미 처리된 경우 건너뜀

    app_detect_flag.add(four_tuple)  # 탐지 완료 플래그 설정

    x_data = {
        "total": packet_data["total"][four_tuple],
        "inbound": packet_data["inbound"][four_tuple],
        "outbound": packet_data["outbound"][four_tuple],
    }

    max_score, max_class = -1, None
    for cls in range(n_classes):
        score = sum((x_data[key] & bitmap_data[key][cls]).count(1) for key in ["total", "inbound", "outbound"])
        if score > max_score:
            max_score, max_class = score, cls

    if max_class is not None:
        socketio.emit("app_detect", (four_tuple[0], four_tuple[1], app_list[max_class]))

def process_packet(packet):
    """
    패킷을 분석하고 데이터를 저장하는 함수
    """
    if IP not in packet:
        return

    src_ip, dst_ip = packet[IP].src, packet[IP].dst
    packet_size = len(packet)

    # 트래픽 데이터 갱신
    for ip in [src_ip, dst_ip]:
        if ip in MONITORING_IP_SET:
            traffic_data[ip] += packet_size

    direction = get_packet_direction(src_ip, dst_ip, MONITORING_IP_SET)
    src_port, dst_port = get_ports(packet)

    if direction == "inbound":
        src_ip, dst_ip = dst_ip, src_ip
        src_port, dst_port = dst_port, src_port

    mac_address = MONITORING_MAC_DICT.get(src_ip, "Unknown")
    four_tuple = (mac_address, src_ip, src_port, dst_ip, dst_port)

    # 패킷 데이터 저장
    packet_data["total"][four_tuple].append(packet_size)
    packet_data[direction][four_tuple].append(packet_size)

    # 패킷 개수가 기준 이상이면 애플리케이션 탐지 실행
    if len(packet_data["total"][four_tuple]) > MIN_PACKET_COUNT:
        classify_packet(four_tuple)

def update_mac_address():
    """
    모니터링 대상의 MAC 주소를 주기적으로 갱신하는 함수
    """
    while True:
        for ip in MONITORING_IP_SET:
            MONITORING_MAC_DICT[ip] = get_mac_address(ip) or "Unknown"
        socketio.emit("update_mac", MONITORING_MAC_DICT)
        time.sleep(UPDATE_MAC_INTERVAL)

def packet_sniffer():
    """
    지정된 IP에 대해 패킷을 캡처하는 스레드 실행 함수
    """
    filter_str = " or ".join(f"host {ip}" for ip in MONITORING_IP_SET)
    sniff(prn=process_packet, filter=filter_str, store=False)

def calculate_throughput():
    """
    초당 트래픽량(Throughput)을 계산하고 전송하는 함수
    """
    while True:
        for ip in MONITORING_IP_SET:
            throughput_data[ip] = traffic_data[ip] - prev_traffic_data[ip]
            prev_traffic_data[ip] = traffic_data[ip]

        socketio.emit("update_traffic", throughput_data)
        time.sleep(1)  # 1초마다 업데이트

# ======================== #
#          ROUTES         #
# ======================== #

@app.route("/")
def index():
    return render_template("index.html")

# ======================== #
#      APP 실행 코드       #
# ======================== #

if __name__ == "__main__":
    # 스레드 실행
    threading.Thread(target=packet_sniffer, daemon=True).start()
    threading.Thread(target=calculate_throughput, daemon=True).start()
    threading.Thread(target=update_mac_address, daemon=True).start()

    socketio.run(app, host="0.0.0.0", port=5001, debug=True)