from flask import Flask, render_template
from flask_socketio import SocketIO
from scapy.all import sniff, IP, TCP, UDP
from collections import defaultdict
from bitarray import bitarray
from ipwhois import IPWhois
from utils import get_packet_direction
import pyshark
import threading
import time
import os
import sys
import pickle
import json
import numpy as np
import asyncio

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
TARGET_APPLICATION = ip_config.get("target_application", {})

# 설정 값
UPDATE_MAC_INTERVAL = 10  # MAC 주소 갱신 주기 (초)
DISC_RANGE = 13  # 이산화 구간
interface = "이더넷"

mac_list = []
sni_dir = {}

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
with open('best_res.pkl', 'rb') as f:
    application_detect = pickle.load(f)

app_list = application_detect['class']
n_classes = len(app_list)
#n_fold = application_detect['N_FOLD']
bitmap_data = {
    "total": application_detect['bitmap'][0],
    "inbound": application_detect['bitmap'][1],
    "outbound": application_detect['bitmap'][2]
}
N_GRAM = application_detect['N_GRAM']
VEC_LEN = application_detect['VEC_LEN']
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
        return  None, None # 이미 탐지된 경우 건너뜀

    app_detect_flag.add(flow_key)

    X = {
        "total": packet_data["total"][flow_key],
        "inbound": packet_data["inbound"][flow_key],
        "outbound": packet_data["outbound"][flow_key],
    }

    # 🔹 각 클래스별 점수 계산
    class_scores = {cls: {"total": 0, "inbound": 0, "outbound": 0, "sum": 0} for cls in range(n_classes)}

    x_data = {key: embedding_packet(X[key]) for key in ["total", "inbound", "outbound"]}

    # 🔹 각 클래스별 점수 계산
    class_scores = {
        cls: sum((x_data[key] & bitmap_data[key][cls]).count(1) for key in ["total", "inbound", "outbound"])
        for cls in range(n_classes)
    }

    # 🔹 최고 점수와 해당 클래스 찾기
    max_class, max_score = max(class_scores.items(), key=lambda item: item[1], default=(None, 0))

    return max_class, max_score

def process_packet(packet):
    """
    패킷을 분석하고 데이터를 저장하는 함수
    """
    try:
        if hasattr(packet, "ip"):
            src_ip = packet.ip.src
            dst_ip = packet.ip.dst
            packet_size = int(packet.ip.len) - int(packet.ip.hdr_len)
        else:
            return
        
        if hasattr(packet, "tcp"):
            src_port = packet.tcp.srcport
            dst_port = packet.tcp.dstport
            protocol = 6
        elif hasattr(packet, "udp"):
            src_port = packet.udp.srcport
            dst_port = packet.udp.dstport
            protocol = 17
        else:
            return        

        # 트래픽 데이터 갱신
        for ip in [src_ip, dst_ip]:
            if ip in MONITORING_IP_SET:
                traffic_data[ip] += packet_size

        direction = get_packet_direction(src_ip, dst_ip, MONITORING_IP_SET)

        if direction == "inbound":
            src_ip, dst_ip = dst_ip, src_ip
            src_port, dst_port = dst_port, src_port
        else:
            packet_size = -packet_size
        
        if hasattr(packet, "eth"):
            src_mac = packet.eth.src
            if MONITORING_MAC_DICT.get(src_ip) != src_mac:
                MONITORING_MAC_DICT[src_ip] = src_mac
                socketio.emit("update_mac", [src_ip, src_mac])
        
        flow_key = (src_ip, src_port, dst_ip, dst_port, protocol)

         # TLS 패킷인지 확인
        if hasattr(packet, 'tls'):
            # TLS 핸드셰이크 메시지 확인
            if hasattr(packet.tls, 'handshake_extensions_server_name'):
                sni_value = packet.tls.handshake_extensions_server_name
                sni_dir[flow_key] = sni_value
        
        packet_data["total"][flow_key].append(packet_size)
        packet_data[direction][flow_key].append(packet_size)

        # 최소 패킷 개수 조건 충족 시 애플리케이션 탐지 실행
        if len(packet_data["total"][flow_key]) > VEC_LEN:
            max_class, score = classify_packet(flow_key)
            if max_class is not None:
                print(f"[DEBUG] flow_key={flow_key}, max_class={app_list[max_class]}, score={score}, sni={sni_dir.get(flow_key)}")
                socketio.emit("app_detect", [flow_key[0], app_list[max_class]])
    except Exception as e:
        print(f"[오류] 패킷 처리 중 오류 발생: {e}")

def generate_ip_filter(ip_set):
    """
    IP 주소에 대한 필터를 생성하는 함수
    """
    if not ip_set:
        return None
    
    filter_condition = " || ".join(f"ip.addr == {ip}" for ip in ip_set)
    return filter_condition


def packet_sniffer():
    """
    지정된 IP에 대해 패킷을 캡처하는 스레드 실행 함수
    """
    asyncio.set_event_loop(asyncio.new_event_loop())  # 새로운 이벤트 루프 생성
    display_filter = generate_ip_filter(MONITORING_IP_SET)
    capture = pyshark.LiveCapture(interface=interface, display_filter=display_filter)

    for packet in capture.sniff_continuously():
        try:
            process_packet(packet)
        except Exception as e:
            print(f"[오류] 패킷 처리 중 오류 발생: {e}")

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

@app.route("/traffic/<ip>")
def traffic_detail(ip):
    """
    특정 IP의 트래픽 정보를 반환하는 페이지
    """
    if ip not in MONITORING_IP_SET:
        return render_template("error.html", message="해당 IP는 모니터링되지 않습니다.")

    # 트래픽 데이터 가져오기
    data = {
        "ip": ip,
        "current_traffic": traffic_data.get(ip, 0),
        "previous_traffic": prev_traffic_data.get(ip, 0),
        "throughput": throughput_data.get(ip, 0),
        "mac_address": MONITORING_MAC_DICT.get(ip, "Unknown"),
    }

    return render_template("traffic_detail.html", data=data)


# ======================== #
#      APP 실행 코드       #
# ======================== #

if __name__ == "__main__":
    threading.Thread(target=packet_sniffer, daemon=True).start()
    threading.Thread(target=calculate_throughput, daemon=True).start()

    socketio.run(app, host="0.0.0.0", port=5002, debug=True)