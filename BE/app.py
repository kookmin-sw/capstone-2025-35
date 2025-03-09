from flask import Flask, render_template
from flask_socketio import SocketIO
from pyshark_sniffer import PysharkSniffer
from config import INTERFACE, BITMAP_PATH, MONITORING_IP_LIST
import threading

# Flask 및 WebSocket 설정
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

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
    if ip not in MONITORING_IP_LIST:
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
    sniffer = PysharkSniffer(interface=INTERFACE, bitmap_path=BITMAP_PATH)
    threading.Thread(target=sniffer.start_sniffing(), daemon=True).start()

    socketio.run(app, host="0.0.0.0", port=5002, debug=True)