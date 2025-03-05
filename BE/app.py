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
import datetime

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
interface = "en0" # 기기별로 다름

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
packet_history = defaultdict(lambda: defaultdict(list))

# Bitmap 데이터 로드
with open('bitmap_record.pkl', 'rb') as f:
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
DISC_RANGE = 13  # 이산화 구간

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
    class_scores = {cls: {"total": 0, "inbound": 0, "outbound": 0, "score": 0} for cls in range(n_classes)}

    x_data = {key: embedding_packet(X[key]) for key in ["total", "inbound", "outbound"]}

    # 🔹 각 클래스별 점수 계산
    class_scores = {
        cls: sum((x_data[key] & bitmap_data[key][cls]).count(1) for key in ["total", "inbound", "outbound"])
        for cls in range(n_classes)
    }
    # 🔹 최고 점수와 해당 클래스 찾기
    max_class, max_score = max(class_scores.items(), key=lambda item: item[1], default=(None, 0))

    return max_class, max_score

def request_mac_address(ip):
    """
    서버의 MAC 주소를 요청하는 함수
    """
    socketio.emit("request_mac", ip)

@socketio.on("receive_mac")
def receive_mac_address(data):
    """
    MAC 주소를 수신하는 함수
    """
    if not isinstance(data, dict):
        return
    if "ip" not in data or "mac" not in data:
        print(f"[ERROR] 데이터에 'ip' 또는 'mac' 키가 없습니다: {data}")
        return
    ip = data["ip"]
    mac = data["mac"]
    MONITORING_MAC_DICT[ip] = mac

def process_packet(packet):
    """
    패킷을 분석하고 데이터를 저장하는 함수
    """
    try:
        if hasattr(packet, "ip"):
            src_ip = packet.ip.src
            dst_ip = packet.ip.dst
            ip_total_length = int(packet.ip.len)
            ip_header_length = int(packet.ip.hdr_len)
        else:
            return
        
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
        
        # MAC 주소 갱신
        if src_ip in MONITORING_IP_SET:
            if hasattr(packet, "eth"):
                src_mac = packet.eth.src
                request_mac_address(src_ip)
                if MONITORING_MAC_DICT.get(src_ip) != src_mac:
                    socketio.emit("update_mac", [src_ip, src_mac])

        direction = get_packet_direction(src_ip, dst_ip, MONITORING_IP_SET)

        if direction == "inbound":
            src_ip, dst_ip = dst_ip, src_ip
            src_port, dst_port = dst_port, src_port
        else:
            packet_size = -packet_size
        
        flow_key = (src_ip, src_port, dst_ip, dst_port, protocol)

         # TLS 패킷인지 확인
        if hasattr(packet, 'tls'):
            # TLS 핸드셰이크 메시지 확인
            if hasattr(packet.tls, 'handshake_extensions_server_name'):
                sni_value = packet.tls.handshake_extensions_server_name
                sni_dir[flow_key] = sni_value
        
        packet_data["total"][flow_key].append(packet_size)
        packet_data[direction][flow_key].append(packet_size)

        timestamp = datetime.datetime.now()
        packet_history[src_ip][dst_ip].append({"timestamp": timestamp, "size": abs(packet_size)})

        # 최소 패킷 개수 조건 충족 시 애플리케이션 탐지 실행
        if len(packet_data["total"][flow_key]) > VEC_LEN and sni_dir.get(flow_key) is not None:
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

import json

def clean_old_packets():
    """
    오래된 패킷 데이터를 정리하는 함수
    """
    while True:
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)

        # 1분 이상 지난 패킷 삭제
        for src_ip in list(packet_history.keys()):
            for dst_ip in list(packet_history[src_ip].keys()):
                packet_history[src_ip][dst_ip] = [
                    packet for packet in packet_history[src_ip][dst_ip]
                    if packet["timestamp"] > one_minute_ago
                ]

                # 만약 특정 dst_ip의 패킷 리스트가 비어 있으면 삭제
                if not packet_history[src_ip][dst_ip]:
                    del packet_history[src_ip][dst_ip]

            # 만약 src_ip 아래 모든 dst_ip가 삭제되었으면 src_ip도 삭제
            if not packet_history[src_ip]:
                del packet_history[src_ip]

        # JSON 직렬화 가능하도록 datetime -> ISO format 문자열로 변환
        packet_history_dict = {
            src_ip: {
                dst_ip: [{"timestamp": pkt["timestamp"].isoformat(), "size": pkt["size"]} for pkt in packet_list]
                for dst_ip, packet_list in dst_dict.items()
            }
            for src_ip, dst_dict in packet_history.items()
        }

        socketio.emit("update_traffic", packet_history_dict)

        time.sleep(1)  # 1초마다 실행

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
    }

    return render_template("traffic_detail.html", data=data)

# ======================== #
#      APP 실행 코드       #
# ======================== #

if __name__ == "__main__":
    threading.Thread(target=packet_sniffer, daemon=True).start()
    threading.Thread(target=clean_old_packets, daemon=True).start()

    socketio.run(app, host="0.0.0.0", port=5002, debug=True)