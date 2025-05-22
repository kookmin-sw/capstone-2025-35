from flask import Flask, render_template
from flask_socketio import SocketIO
from config import INTERFACE, BITMAP_PATH, MONITORING_IP_LIST, SNIFF_LIB, LOG_PATH, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
import threading
import signal
import os

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

# ======================== #
#      APP 실행 코드       #
# ======================== #

if __name__ == "__main__":
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