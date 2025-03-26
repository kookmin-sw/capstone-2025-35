from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import threading
import time
import random
import json
from datetime import datetime

# Flask 및 WebSocket 설정
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 데모 데이터
MONITORING_IP_LIST = ["192.168.1.100", "192.168.1.101"]
MAC_DICT = {
    "192.168.1.100": "00:1A:2B:3C:4D:5E",
    "192.168.1.101": "AA:BB:CC:DD:EE:FF"
}
STREAMING_SERVICES = {
    "192.168.1.100": ["youtube", "netflix"],
    "192.168.1.101": ["wavve", "coupangplay"]
}

# 전역 변수
start_time = datetime.now()
traffic_data = {ip: [] for ip in MONITORING_IP_LIST}
seconds_passed = 0

# ======================== #
#          ROUTES         #
# ======================== #

@app.route("/")
def index():
    """메인 페이지"""
    return render_template("index.html")

@app.route("/traffic/<ip>")
def traffic_detail(ip):
    """특정 IP의 트래픽 정보를 반환하는 페이지"""
    if ip not in MONITORING_IP_LIST:
        return render_template("error.html", message="해당 IP는 모니터링되지 않습니다.")

    data = {
        "ip": ip,
        "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "detected_services": STREAMING_SERVICES.get(ip, [])
    }

    return render_template("traffic_detail.html", data=data)

# ======================== #
#      데모 데이터 생성     #
# ======================== #

def generate_traffic_data():
    """랜덤 트래픽 데이터 생성"""
    global seconds_passed
    
    while True:
        seconds_passed += 1
        
        # 각 IP에 대한 트래픽 데이터 생성
        for ip in MONITORING_IP_LIST:
            # 기본 트래픽 + 랜덤 노이즈
            base_traffic = 50000  # 50KB 기본값
            noise = random.randint(-20000, 40000)
            
            # 주기적인 트래픽 스파이크 (20초마다)
            if seconds_passed % 20 < 3:
                spike = random.randint(100000, 500000)
            else:
                spike = 0
                
            traffic_value = max(0, base_traffic + noise + spike)
            
            if len(traffic_data[ip]) > 100:
                traffic_data[ip] = traffic_data[ip][-100:]
            
            traffic_data[ip].append(traffic_value)
        
        # 트래픽 데이터 전송
        socketio.emit('traffic_total', {
            'seconds_passed': seconds_passed,
            'traffic_total': traffic_data,
            'detected_services': list(STREAMING_SERVICES.values())[0]  # 데모용
        })
        
        # 상세 트래픽 데이터 전송 (각 IP별)
        for ip in MONITORING_IP_LIST:
            download = random.randint(10000, 100000)
            upload = random.randint(5000, 30000)
            
            socketio.emit('traffic_detail', {
                'ip': ip,
                'download': download,
                'upload': upload
            })
            
            # 프로토콜 통계
            socketio.emit('protocol_stats', {
                'ip': ip,
                'tcp': random.randint(50, 200),
                'udp': random.randint(20, 100),
                'icmp': random.randint(0, 10),
                'other': random.randint(0, 5)
            })
            
            # 포트 통계
            ports = {}
            for port in [80, 443, 8080, 22, 53]:
                ports[port] = random.randint(10, 100)
            
            socketio.emit('port_stats', {
                'ip': ip,
                'ports': ports
            })
            
            # 패킷 로그
            packet = {
                'time': datetime.now().timestamp() * 1000,
                'source': f"192.168.1.{random.randint(1, 254)}",
                'destination': ip,
                'protocol': random.choice(['TCP', 'UDP', 'HTTP', 'DNS']),
                'size': random.randint(64, 1500),
                'info': f"Sample packet info {random.randint(1000, 9999)}"
            }
            
            socketio.emit('packet_log', {
                'ip': ip,
                'packet': packet
            })
        
        # MAC 주소 업데이트
        socketio.emit('mac_update', {
            'mac_dict': MAC_DICT
        })
        
        # 호스트명 업데이트
        for ip in MONITORING_IP_LIST:
            socketio.emit('hostname_update', {
                'ip': ip,
                'hostname': f"host-{ip.split('.')[-1]}.local"
            })
        
        # 스트리밍 서비스 감지
        for ip, services in STREAMING_SERVICES.items():
            socketio.emit('streaming_detection', {
                'ip': ip,
                'services': services
            })
        
        time.sleep(1)  # 1초마다 업데이트

# ======================== #
#      APP 실행 코드       #
# ======================== #

if __name__ == "__main__":
    print("=== 트래픽 모니터링 데모 시작 ===")
    print(f"모니터링 중인 IP: {MONITORING_IP_LIST}")
    print("웹 인터페이스: http://localhost:5002")
    print("종료하려면 Ctrl+C를 누르세요.")
    
    # 데모 데이터 생성 스레드 시작
    threading.Thread(target=generate_traffic_data, daemon=True).start()
    
    # 웹 서버 시작
    socketio.run(app, host="0.0.0.0", port=5002, debug=False)