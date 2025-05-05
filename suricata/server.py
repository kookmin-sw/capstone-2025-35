from flask import Flask
import subprocess
import threading
import time
import json
import os

app = Flask(__name__)
EVE_LOG_PATH = "/var/log/suricata/eve.json"

# Suricata 로그에서 5-tuple 추출
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
            "suricata", "-c", "/etc/suricata/suricata.yaml", "-i", "자기 네트워크 인터페이스"
        ])
        print("[INFO] Suricata 실행됨")

        # 로그 감시 쓰레드 시작
        t = threading.Thread(target=monitor_suricata_logs, daemon=True)
        t.start()

        return "Suricata 실행됨. alert 감시 중입니다."
    except Exception as e:
        return f"Suricata 실행 실패: {str(e)}"

# Suricata 정지
@app.route("/stop-suricata", methods=["POST"])
def stop_suricata():
    try:
        subprocess.run(["pkill", "-f", "suricata"], check=True)
        print("[INFO] Suricata 프로세스 종료됨")
        return "Suricata가 정지되었습니다."
    except subprocess.CalledProcessError:
        return "Suricata 정지 실패: 이미 종료되었거나 실행 중이 아닙니다."

# 웹 UI 라우트
@app.route("/")
def index():
    return '''
    <html>
    <head><title>Suricata IDS</title></head>
    <body>
        <h2>Suricata IDS 제어</h2>
        <button onclick="startSuricata()">차단</button>
        <button onclick="stopSuricata()">정지</button>

        <script>
        function startSuricata() {
            fetch('/start-suricata', { method: 'POST' })
                .then(res => res.text())
                .then(msg => alert(msg))
                .catch(err => alert('오류: ' + err));
        }
        function stopSuricata() {
            fetch('/stop-suricata', { method: 'POST' })
                .then(res => res.text())
                .then(msg => alert(msg))
                .catch(err => alert('오류: ' + err));
        }
        </script>
    </body>
    </html>
    '''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
