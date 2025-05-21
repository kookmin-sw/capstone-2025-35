import subprocess
from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import signal
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from config import INTERFACE, BITMAP_PATH, MONITORING_IP_LIST, SNIFF_LIB, LOG_PATH, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
except ImportError:
    print("config가 설정되지 않았습니다.")
    # Prompt user for interface and IP list at runtime
    from create_config import create_config, prompt_for_ip_and_interface
    INTERFACE, MONITORING_IP_LIST = prompt_for_ip_and_interface()
    from config import INTERFACE, BITMAP_PATH, MONITORING_IP_LIST, SNIFF_LIB, LOG_PATH, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS


from DB import init_db, db
from DB.models import PacketLog

# Flask 및 WebSocket 설정
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# DB init
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
init_db(app)

# ======================== #
#           ENDS           #
# ======================== #

def signal_handler(sig, frame, sniffer, LOG_PATH):
    print("프로그램 종료")

    sniffer.visualization(LOG_PATH)
    exit(0)

# ======================== #
#          ROUTES          #
# ======================== #

@app.route("/")
def index():
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
    }

    return render_template("traffic_detail.html", data=data)

@socketio.on('join_traffic_detail')
def handle_join_traffic_detail(data):
    """
    클라이언트가 트래픽 상세 페이지에 접속할 때 호출되는 이벤트 핸들러
    """
    ip = data['ip']
    sniffer.hostname(ip)
    threading.Thread(target=sniffer.run_loop, daemon=True).start()


# 수정본 
# 차단 버튼 서버 요청 
@socketio.on('get_detected_sessions') 
def handle_get_detected_sessions():
    sniffer.send_detected_sessions()


@socketio.on('run_suricata')
def handle_run_suricata():
    try:
        # Suricata 실행 (경로 및 옵션 환경에 맞게 조정)
        result = subprocess.run(
            ['suricata', '-c', '/etc/suricata/suricata.yaml', '-i', 'eth0'],
            capture_output=True,
            text=True,
            timeout=60  # 필요에 따라 조정
        )

        if result.returncode == 0:
            socketio.emit('suricata_status', {'success': True, 'message': result.stdout})
        else:
            socketio.emit('suricata_status', {'success': False, 'message': result.stderr})
    except Exception as e:
        socketio.emit('suricata_status', {'success': False, 'message': str(e)})

#수리카타 로그 추적, 이건 수리카타를 사용하신다고 하길래 혹시나 해서 추가합니다 환경에 따라 수정하고 쓰시면 됩니다
EVE_LOG_PATH = "/var/log/suricata/eve.json" 
def monitor_suricata_logs():
    if not os.path.exists(EVE_LOG_PATH):
        print(f"[오류] 로그 파일이 존재하지 않음: {EVE_LOG_PATH}")
        return
    print("[INFO] Suricata alert 로그 감시 시작")

    with open(EVE_LOG_PATH, "r") as f:
        f.seek(0, 2)  # 로그 끝으로 이동
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            try:
                log = json.loads(line)
                if log.get("event_type") == "alert":
                    five_tuple = {
                        "src_ip": log.get("src_ip"),
                        "dst_ip": log.get("dest_ip"),
                        "src_port": log.get("src_port"),
                        "dst_port": log.get("dest_port"),
                        "protocol": log.get("proto")
                    }
                    print("[ALERT] 5-tuple 감지:", five_tuple)
            except json.JSONDecodeError:
                continue

# Suricata 실행
@app.route("/start-suricata", methods=["POST"])
def start_suricata():
    try:
        subprocess.Popen([
            "suricata", "-c", "/etc/suricata/suricata.yaml", "-i", "wlp61s0"
        ])
        print("[INFO] Suricata 실행됨")

        # 로그 감시 쓰레드 시작
        t = threading.Thread(target=monitor_suricata_logs, daemon=True)
        t.start()

        return "Suricata 실행됨. alert 감시 중입니다."
    except Exception as e:
        return f"Suricata 실행 실패: {str(e)}"

# Suricata 정지 이건 만약 차단 해제할때 쓸 수 있을 까봐 추가 
#필요 없으면 지우면 됩니다
@app.route("/stop-suricata", methods=["POST"])
def stop_suricata():
    try:
        subprocess.run(["pkill", "-f", "suricata"], check=True)
        print("[INFO] Suricata 프로세스 종료됨")
        return "Suricata가 정지되었습니다."
    except subprocess.CalledProcessError:
        return "Suricata 정지 실패: 이미 종료되었거나 실행 중이 아닙니다."
#수정 끝

# ======================== #
#      APP 실행 코드       #
# ======================== #

if __name__ == "__main__":
    if MONITORING_IP_LIST == None:
        print("config.py에 MONITORING_IP_LIST가 설정되지 않았습니다.")
        # Prompt user for interface and IP list at runtime
        INTERFACE, MONITORING_IP_LIST = prompt_for_ip_and_interface()
        print("config.py를 생성했습니다. 다시 실행해주세요.")
    
    if SNIFF_LIB == "pyshark":
        from pyshark_sniffer import PysharkSniffer
        sniffer = PysharkSniffer(socketio=socketio, app=app, interface=INTERFACE, bitmap_path=BITMAP_PATH)
    elif SNIFF_LIB == "scapy":
        from scapy_sniffer import ScapySniffer
        sniffer = ScapySniffer(socketio=socketio, app=app, interface=INTERFACE, bitmap_path=BITMAP_PATH)
    threading.Thread(target=sniffer.start_sniffing, daemon=True).start()
    threading.Thread(target=sniffer.monitor_traffic, daemon=True).start()

    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, sniffer, LOG_PATH))
    socketio.run(app, host="0.0.0.0", port=5002, debug=False)