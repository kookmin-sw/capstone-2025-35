from flask import Flask, render_template
from flask_socketio import SocketIO
from scapy.all import sniff, IP
from collections import defaultdict
from bitarray import bitarray
from utils import get_mac_address, get_packet_direction, get_ports
import threading
import time
import os
import sys
import pickle
import json
import numpy as np

# Flask 및 WebSocket 설정
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# JSON 파일 경로 및 로드
json_file = "monitoring_ip.json"

if not os.path.exists(json_file):
    sys.exit("\n[오류] monitoring_ip.json 파일이 존재하지 않습니다.\n"
             "`python create_ip_json.py` 명령을 실행하여 모니터링할 IP를 추가하세요.")

with open(json_file, "r") as f:
    ip_config = json.load(f)

MONITORING_IP_SET = set(ip_config.get("MONITORING_IP", ["192.168.1.1"]))
MONITORING_MAC_DICT = {}

# 설정 값
UPDATE_MAC_INTERVAL = 10  # MAC 주소 갱신 주기 (초)
MIN_PACKET_COUNT = 100  # 최소 패킷 개수 (탐지 기준)
DISC_RANGE = 13  # 이산화 구간

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
VEC_LEN = application_detect['VEC_LEN']
N_GRAM = application_detect['N_GRAM']
disc = application_detect['disc']


# ======================== #
#       HELPER 함수        #
# ======================== #

def discretize_values(value, disc_range):
    """
    값을 이산화하는 함수
    """
    if value == 0:
        return DISC_RANGE
    return np.searchsorted(disc_range, value, side='right') - 1 + (1 if value > 0 else 0)


def embedding_packet(packet_seq):
    """
    패킷 데이터를 비트맵으로 변환하는 함수
    """
    dr = len(disc)
    L = dr ** N_GRAM
    res = bitarray(L)
    res.setall(0)  # 초기화

    discretized_data = [discretize_values(val, disc) for val in packet_seq]

    for idx in range(0, min(len(discretized_data), VEC_LEN) - N_GRAM + 1):
        n_gram = discretized_data[idx:idx + N_GRAM]
        pos = sum((dr ** i) * val for i, val in enumerate(reversed(n_gram)))
        res[pos] = 1

    return res


def classify_packet(flow_key):
    """
    패킷 데이터를 기반으로 애플리케이션을 식별하는 함수
    """
    if flow_key in app_detect_flag:
        return  # 이미 탐지된 경우 건너뜀

    app_detect_flag.add(flow_key)

    X = {
        "total": packet_data["total"][flow_key],
        "inbound": packet_data["inbound"][flow_key],
        "outbound": packet_data["outbound"][flow_key],
    }

    x_data = {key: embedding_packet(X[key]) for key in ["total", "inbound", "outbound"]}

    max_class = max(
        range(n_classes),
        key=lambda cls: sum((x_data[key] & bitmap_data[key][cls]).count(1) for key in ["total", "inbound", "outbound"]),
        default=None
    )

    if max_class is not None:
        socketio.emit("app_detect", [flow_key[1], app_list[max_class]])


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
    flow_key = (mac_address, src_ip, src_port, dst_ip, dst_port)

    # 패킷 데이터 저장
    packet_data["total"][flow_key].append(packet_size)
    packet_data[direction][flow_key].append(packet_size)

    # 최소 패킷 개수 조건 충족 시 애플리케이션 탐지 실행
    if len(packet_data["total"][flow_key]) > MIN_PACKET_COUNT:
        classify_packet(flow_key)


def update_mac_addresses():
    """
    모니터링 대상 IP의 MAC 주소를 주기적으로 갱신하는 함수
    """
    while True:
        MONITORING_MAC_DICT.update({ip: get_mac_address(ip) or "Unknown" for ip in MONITORING_IP_SET})
        socketio.emit("update_mac", MONITORING_MAC_DICT)
        time.sleep(UPDATE_MAC_INTERVAL)


def packet_sniffer():
    """
    지정된 IP에 대해 패킷을 캡처하는 스레드 실행 함수
    """
    filter_str = " or ".join(f"host {ip}" for ip in MONITORING_IP_SET) if MONITORING_IP_SET else None
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
    threading.Thread(target=packet_sniffer, daemon=True).start()
    threading.Thread(target=calculate_throughput, daemon=True).start()
    threading.Thread(target=update_mac_addresses, daemon=True).start()

    socketio.run(app, host="0.0.0.0", port=5002, debug=True)