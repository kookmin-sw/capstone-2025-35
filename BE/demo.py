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
MONITORING_IP_LIST = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]
MAC_DICT = {
    "192.168.1.100": "00:1A:2B:3C:4D:5E",
    "192.168.1.101": "AA:BB:CC:DD:EE:FF",
    "192.168.1.102": "11:22:33:44:55:66"
}
STREAMING_SERVICES = {
    "192.168.1.100": ["youtube", "netflix"],
    "192.168.1.101": ["wavve", "coupangplay"],
    "192.168.1.102": ["navertv"]
}
HOSTNAMES = {
    "192.168.1.100": "desktop-pc.local",
    "192.168.1.101": "smartphone.local",
    "192.168.1.102": "smart-tv.local"
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
        "detected_services": STREAMING_SERVICES.get(ip, []),
        "mac_address": MAC_DICT.get(ip, "Unknown"),
        "hostname": HOSTNAMES.get(ip, "Unknown")
    }

    # 트래픽 상세 페이지에 필요한 초기 데이터 전송
    # 이 데이터는 페이지 로드 시 즉시 사용 가능하도록 함
    traffic_detail_data = {
        "ip": ip,
        "download": random.randint(10000, 100000),
        "upload": random.randint(5000, 30000)
    }
    
    protocol_stats_data = {
        "ip": ip,
        "tcp": random.randint(50, 200),
        "udp": random.randint(20, 100),
        "icmp": random.randint(0, 10),
        "other": random.randint(0, 5)
    }
    
    ports_data = {}
    common_ports = [80, 443, 8080, 22, 53, 3389, 21, 25, 110, 143]
    for port in common_ports:
        ports_data[port] = random.randint(10, 100)
    
    port_stats_data = {
        "ip": ip,
        "ports": ports_data
    }

    return render_template("traffic_detail.html", data=data)

# ======================== #
#     SOCKET.IO 이벤트     #
# ======================== #

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결 시 호출되는 이벤트 핸들러"""
    print("클라이언트가 연결되었습니다.")

@socketio.on('join_traffic_detail')
def handle_join_traffic_detail(data):
    """트래픽 상세 페이지에 접속했을 때 호출되는 이벤트 핸들러"""
    if 'ip' not in data:
        return
    
    ip = data['ip']
    if ip not in MONITORING_IP_LIST:
        return
    
    print(f"클라이언트가 {ip}의 트래픽 상세 페이지에 접속했습니다.")
    
    # 초기 데이터 전송
    # MAC 주소 정보
    socketio.emit('mac_update', {
        'mac_dict': MAC_DICT
    })
    
    # 호스트명 정보
    socketio.emit('hostname_update', {
        'ip': ip,
        'hostname': HOSTNAMES.get(ip, "Unknown")
    })
    
    # 트래픽 상세 정보
    socketio.emit('traffic_detail', {
        'ip': ip,
        'download': random.randint(10000, 100000),
        'upload': random.randint(5000, 30000)
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
    common_ports = [80, 443, 8080, 22, 53, 3389, 21, 25, 110, 143]
    for port in common_ports:
        ports[port] = random.randint(10, 100)
    
    socketio.emit('port_stats', {
        'ip': ip,
        'ports': ports
    })
    
    # 스트리밍 서비스 정보
    socketio.emit('streaming_detection', {
        'ip': ip,
        'services': STREAMING_SERVICES.get(ip, [])
    })

# ======================== #
#      데모 데이터 생성     #
# ======================== #

def generate_traffic_pattern(time_passed, base_traffic=50000, noise_level=20000):
    """시간에 따른 트래픽 패턴 생성"""
    # 기본 트래픽 + 랜덤 노이즈
    noise = random.randint(-noise_level, noise_level)
    
    # 주기적인 트래픽 스파이크 (20초마다)
    if time_passed % 20 < 3:
        spike = random.randint(100000, 500000)
    else:
        spike = 0
    
    # 시간대별 패턴 (낮에는 트래픽이 더 많음)
    hour = datetime.now().hour
    time_factor = 1.0
    if 9 <= hour <= 18:  # 업무 시간
        time_factor = 1.5
    elif 19 <= hour <= 23:  # 저녁 시간 (스트리밍 많음)
        time_factor = 2.0
    elif 0 <= hour <= 5:  # 새벽 (트래픽 적음)
        time_factor = 0.5
    
    traffic_value = max(0, int((base_traffic + noise + spike) * time_factor))
    return traffic_value

def generate_traffic_data():
    """랜덤 트래픽 데이터 생성"""
    global seconds_passed
    
    while True:
        seconds_passed += 1
        
        # 각 IP에 대한 트래픽 데이터 생성
        for ip in MONITORING_IP_LIST:
            # IP별로 다른 트래픽 패턴 생성
            if ip == "192.168.1.100":  # 데스크톱 PC (높은 트래픽)
                base_traffic = 80000
                noise_level = 30000
            elif ip == "192.168.1.101":  # 스마트폰 (중간 트래픽)
                base_traffic = 40000
                noise_level = 15000
            else:  # 스마트 TV (낮은 트래픽, 가끔 스파이크)
                base_traffic = 20000
                noise_level = 10000
                
            traffic_value = generate_traffic_pattern(seconds_passed, base_traffic, noise_level)
            
            if len(traffic_data[ip]) > 100:
                traffic_data[ip] = traffic_data[ip][-100:]
            
            traffic_data[ip].append(traffic_value)
        
        # 트래픽 데이터 전송
        socketio.emit('traffic_total', {
            'seconds_passed': seconds_passed,
            'traffic_total': traffic_data,
            'detected_services': list(STREAMING_SERVICES.values())[0]  # 데모용
        })
        
        # MAC 주소 업데이트 (10초마다)
        if seconds_passed % 10 == 0:
            socketio.emit('mac_update', {
                'mac_dict': MAC_DICT
            })
        
        # 호스트명 업데이트 (15초마다)
        if seconds_passed % 15 == 0:
            for ip in MONITORING_IP_LIST:
                socketio.emit('hostname_update', {
                    'ip': ip,
                    'hostname': HOSTNAMES[ip]
                })
        
        # 스트리밍 서비스 감지 (30초마다)
        if seconds_passed % 30 == 0:
            for ip, services in STREAMING_SERVICES.items():
                socketio.emit('streaming_detection', {
                    'ip': ip,
                    'services': services
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
            
            # 프로토콜 통계 (5초마다)
            if seconds_passed % 5 == 0:
                socketio.emit('protocol_stats', {
                    'ip': ip,
                    'tcp': random.randint(50, 200),
                    'udp': random.randint(20, 100),
                    'icmp': random.randint(0, 10),
                    'other': random.randint(0, 5)
                })
            
            # 포트 통계 (8초마다)
            if seconds_passed % 8 == 0:
                ports = {}
                common_ports = [80, 443, 8080, 22, 53, 3389, 21, 25, 110, 143]
                for port in common_ports:
                    ports[port] = random.randint(10, 100)
                
                socketio.emit('port_stats', {
                    'ip': ip,
                    'ports': ports
                })
            
            # 패킷 로그 (2초마다)
            if seconds_passed % 2 == 0:
                protocols = ['TCP', 'UDP', 'HTTP', 'DNS', 'HTTPS', 'ICMP']
                protocol = random.choice(protocols)
                
                # 프로토콜에 따른 정보 생성
                if protocol == 'TCP':
                    info = random.choice(['SYN', 'ACK', 'SYN-ACK', 'FIN', 'RST'])
                elif protocol == 'UDP':
                    info = f"Source Port: {random.randint(1024, 65535)}, Dest Port: {random.randint(1, 1023)}"
                elif protocol == 'HTTP':
                    info = random.choice(['GET /', 'POST /api', 'PUT /data', 'DELETE /resource'])
                elif protocol == 'DNS':
                    info = random.choice(['A Record Query', 'AAAA Record Query', 'MX Record Query', 'Response'])
                elif protocol == 'HTTPS':
                    info = random.choice(['TLS Handshake', 'Client Hello', 'Server Hello', 'Certificate'])
                else:  # ICMP
                    info = random.choice(['Echo Request', 'Echo Reply', 'Destination Unreachable'])
                
                packet = {
                    'time': datetime.now().timestamp() * 1000,
                    'source': f"192.168.1.{random.randint(1, 254)}",
                    'destination': ip,
                    'protocol': protocol,
                    'size': random.randint(64, 1500),
                    'info': info
                }
                
                # 패킷 로그 데이터 전송
                packet_data = {
                    'ip': ip,
                    'packet': packet
                }
                socketio.emit('packet_log', packet_data)
        
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