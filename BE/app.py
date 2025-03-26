from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from config import INTERFACE, BITMAP_PATH, MONITORING_IP_LIST, SNIFF_LIB, TARGET_APPLICATIONS
import threading
import time
import socket
import os
from datetime import datetime

# Flask 및 WebSocket 설정
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 전역 변수
start_time = datetime.now()
detected_services = {}  # IP별 감지된 스트리밍 서비스

# ======================== #
#          socket         #
# ======================== #

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결 시 호출"""
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제 시 호출"""
    print(f"Client disconnected: {request.sid}")

# ======================== #
#          ROUTES         #
# ======================== #

@app.route("/")
def index():
    """메인 페이지"""
    return render_template("index.html")

@app.route("/traffic/<ip>")
def traffic_detail(ip):
    """
    특정 IP의 트래픽 정보를 반환하는 페이지
    """
    if ip not in MONITORING_IP_LIST:
        return render_template("error.html", message="해당 IP는 모니터링되지 않습니다.")

    # 트래픽 데이터 가져오기
    data = {
        "ip": ip,
        "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "detected_services": detected_services.get(ip, [])
    }

    return render_template("traffic_detail.html", data=data)

@app.route("/api/status")
def api_status():
    """API 상태 확인"""
    return jsonify({
        "status": "running",
        "uptime": (datetime.now() - start_time).total_seconds(),
        "monitoring_ips": MONITORING_IP_LIST,
        "interface": INTERFACE,
        "sniff_lib": SNIFF_LIB
    })

@app.route("/api/applications")
def api_applications():
    """모니터링 중인 애플리케이션 목록"""
    return jsonify({
        "applications": TARGET_APPLICATIONS
    })

# ======================== #
#     헬퍼 함수들          #
# ======================== #

def detect_streaming_services(ip, domain):
    """도메인 기반으로 스트리밍 서비스 감지"""
    for domain_pattern, service_name in TARGET_APPLICATIONS.items():
        if domain_pattern in domain:
            if ip not in detected_services:
                detected_services[ip] = []
            
            if service_name not in detected_services[ip]:
                detected_services[ip].append(service_name)
                socketio.emit('streaming_detection', {
                    'ip': ip,
                    'services': detected_services[ip]
                })
            return True
    return False

def get_hostname(ip):
    """IP 주소로부터 호스트명 조회"""
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname
    except:
        return None

# ======================== #
#      APP 실행 코드       #
# ======================== #

if __name__ == "__main__":
    if SNIFF_LIB == "pyshark":
        from pyshark_sniffer import PysharkSniffer
        sniffer = PysharkSniffer(socketio=socketio, interface=INTERFACE, bitmap_path=BITMAP_PATH)
    elif SNIFF_LIB == "scapy":
        from scapy_sniffer import ScapySniffer
        sniffer = ScapySniffer(socketio=socketio, interface=INTERFACE, bitmap_path=BITMAP_PATH)
    
    # 스니퍼에 스트리밍 서비스 감지 콜백 등록
    if hasattr(sniffer, 'set_domain_callback'):
        sniffer.set_domain_callback(detect_streaming_services)
    
    # 스니핑 및 모니터링 스레드 시작
    threading.Thread(target=sniffer.start_sniffing, daemon=True).start()
    threading.Thread(target=sniffer.monitor_traffic, daemon=True).start()
    
    # 호스트명 조회 스레드
    def update_hostnames():
        while True:
            for ip in MONITORING_IP_LIST:
                hostname = get_hostname(ip)
                if hostname:
                    socketio.emit('hostname_update', {
                        'ip': ip,
                        'hostname': hostname
                    })
            time.sleep(300)  # 5분마다 업데이트
    
    threading.Thread(target=update_hostnames, daemon=True).start()
    
    socketio.run(app, host="0.0.0.0", port=5002, debug=False)