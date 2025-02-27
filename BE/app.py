from flask import Flask, render_template
from flask_socketio import SocketIO
from scapy.all import sniff, IP, TCP, UDP
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

# JSON 파일 로드
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
MIN_PACKET_COUNT = 20  # 최소 패킷 개수 (탐지 기준)

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

def get_protocol(packet):
    """
    패킷의 프로토콜을 반환 (TCP: 6, UDP: 17)
    """
    if TCP in packet:
        return 6  # TCP
    elif UDP in packet:
        return 17  # UDP
    return 0  # 기타


def classify_packet(flow_key):
    """
    5-Tuple 기반 패킷 분류 및 애플리케이션 탐지
    """
    if flow_key in app_detect_flag:
        return  # 이미 탐지된 경우 건너뜀

    app_detect_flag.add(flow_key)

    X = {
        "total": packet_data["total"][flow_key],
        "inbound": packet_data["inbound"][flow_key],
        "outbound": packet_data["outbound"][flow_key],
    }

    x_data = {key: bitarray(VEC_LEN) for key in ["total", "inbound", "outbound"]}

    for key in ["total", "inbound", "outbound"]:
        x_data[key].setall(0)
        if len(X[key]) >= N_GRAM:
            for i in range(len(X[key]) - N_GRAM + 1):
                n_gram = X[key][i:i + N_GRAM]
                pos = sum((len(disc) ** j) * v for j, v in enumerate(reversed(n_gram)))
                x_data[key][pos] = 1

    class_scores = {
        cls: sum((x_data[key] & bitmap_data[key][cls]).count(1) for key in ["total", "inbound", "outbound"])
        for cls in range(n_classes)
    }

    max_class, max_score = max(class_scores.items(), key=lambda item: item[1], default=(None, 0))

    if max_class is not None:
        print(f"[DEBUG] flow_key={flow_key}, max_class={app_list[max_class]}, score={max_score}")
        socketio.emit("app_detect", [flow_key[0], app_list[max_class], max_score])


def process_packet(packet):
    """
    패킷을 분석하고 5-Tuple 데이터를 저장
    """
    if IP not in packet:
        return

    src_ip, dst_ip = packet[IP].src, packet[IP].dst
    protocol = get_protocol(packet)  # TCP = 6, UDP = 17

    # 패킷 페이로드 길이 계산
    if TCP in packet or UDP in packet:
        payload_length = len(packet[IP].payload)  # TCP/UDP 페이로드 크기
    else:
        payload_length = packet[IP].len - (packet[IP].ihl * 4)  # 일반 IP 패킷 페이로드 크기

    # 트래픽 데이터 갱신
    for ip in [src_ip, dst_ip]:
        if ip in MONITORING_IP_SET:
            traffic_data[ip] += payload_length  # 기존 packet_size 대신 payload_length 사용

    direction = get_packet_direction(src_ip, dst_ip, MONITORING_IP_SET)
    src_port, dst_port = get_ports(packet)

    if direction == "inbound":
        src_ip, dst_ip = dst_ip, src_ip
        src_port, dst_port = dst_port, src_port

    mac_address = MONITORING_MAC_DICT.get(src_ip, "Unknown")

    # 🔹 5-Tuple 구조 적용
    flow_key = (src_ip, src_port, dst_ip, dst_port, protocol)

    # 패킷 데이터 저장 (payload_length 사용)
    packet_data["total"][flow_key].append(payload_length)
    packet_data[direction][flow_key].append(payload_length)

    # 최소 패킷 개수 조건 충족 시 애플리케이션 탐지 실행
    if len(packet_data["total"][flow_key]) > MIN_PACKET_COUNT:
        classify_packet(flow_key)


def update_mac_addresses():
    """
    모니터링 대상 IP의 MAC 주소를 주기적으로 갱신
    """
    while True:
        MONITORING_MAC_DICT.update({ip: get_mac_address(ip) or "Unknown" for ip in MONITORING_IP_SET})
        socketio.emit("update_mac", MONITORING_MAC_DICT)
        time.sleep(UPDATE_MAC_INTERVAL)


def packet_sniffer():
    """
    지정된 IP에 대해 패킷을 캡처하는 스레드 실행
    """
    filter_str = " or ".join(f"host {ip}" for ip in MONITORING_IP_SET) if MONITORING_IP_SET else None
    sniff(prn=process_packet, filter=filter_str, store=False)


def calculate_throughput():
    """
    초당 트래픽량(Throughput)을 계산하고 전송
    """
    while True:
        for ip in MONITORING_IP_SET:
            throughput_data[ip] = traffic_data[ip] - prev_traffic_data[ip]
            prev_traffic_data[ip] = traffic_data[ip]

        socketio.emit("update_traffic", throughput_data)
        time.sleep(1)  # 1초마다 업데이트


# ======================== #
#      APP 실행 코드       #
# ======================== #

if __name__ == "__main__":
    threading.Thread(target=packet_sniffer, daemon=True).start()
    threading.Thread(target=calculate_throughput, daemon=True).start()
    threading.Thread(target=update_mac_addresses, daemon=True).start()

    socketio.run(app, host="0.0.0.0", port=5002, debug=True)