from flask import Flask, request, jsonify, render_template
import subprocess
import os
import threading
import time
import json

app = Flask(__name__)

# pf 에서 사용할 앵커 이름 및 경로와 아래에서 사용할 suricata 로그 경로
# /etc/pf.anchors/capstone 에 접근하려면 root 권한이 있어야해서
# 이 코드를 실행할 때 sudo 를 붙여야함
ANCHOR_NAME = "capstone"
ANCHOR_FILE = f"/etc/pf.anchors/{ANCHOR_NAME}"
EVE_LOG_PATH = "/opt/homebrew/var/log/suricata/eve.json"  

# 앵커를 pf 에 로드하는 명령
# pfctl -a capstone -f /etc/pf.anchors/capstone : capstone 파일에서 rule 을 읽어와서 PF 에 적용
def reload_anchor():
    result = subprocess.run(["sudo", "pfctl", "-a", ANCHOR_NAME, "-f", ANCHOR_FILE], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(result.stderr)

# 입력한 ip 주소를 차단하는 rule 을 capstone 파일에 쓰고, pf 에 로드함
def block_ip(ip):
    # 출발지를 기준으로(직접 입력한 IP 혹은 suricata 로 탐지한 서버 IP) 에 대한 패킷을 막는 rule
    rule_out = f"block drop from {ip} to any\n"

    # capstone 파일이 없으면 생성
    if not os.path.exists(ANCHOR_FILE):
        with open(ANCHOR_FILE, "w") as f:
            f.write("")
    
    # capstone 파일을 읽어서 위에서 설정한 rule 이 이미 있는 지 확인
    with open(ANCHOR_FILE, "r") as f:
        rules = f.readlines()

    already_out = any(rule_out.strip() == r.strip() for r in rules)

    # 이미 같은 rule 이 있으면 그냥 return
    if already_out:
        return f"{ip}는 이미 단방향 차단되어 있습니다."
    
    # 새로운 rule 이라면 capstone 파일에 씀
    with open(ANCHOR_FILE, "a") as f:
        if not already_out:
            f.write(rule_out)
    
    # 새로 쓴 rule 을 pf 에 로드
    reload_anchor()
    return f"{ip} 단방향 차단 성공"

# 입력한 ip 주소 차단 해제함(capstone 에서 해당 rule 을 제거하고, pf 다시 로드)
def unblock_ip(ip):
    # 출발지를 기준으로(직접 입력한 IP 혹은 suricata 로 탐지한 서버 IP) 에 대한 패킷을 막는 rule
    rule_out = f"block drop from {ip} to any"

    # 만약 capstone 파일 자체가 없으면 바로 return
    if not os.path.exists(ANCHOR_FILE):
        return f"{ip} 차단 룰 없음\n"

    # capstone 파일을 읽어서 해제하려는 rule 을 제외하고 나머지를 new_rules 에 넣음
    with open(ANCHOR_FILE, "r") as f:
        rules = f.readlines()

    # new_rules 를 적음(해제하는 rule 을 제외한 나머지 rule)
    new_rules = [r for r in rules if rule_out not in r]
    with open(ANCHOR_FILE, "w") as f:
        f.writelines(new_rules)
    
    # rule 을 해제한 상태에서 로드
    reload_anchor()
    return f"{ip} 단방향 차단 해제\n"

# Suricata alert 로그 모니터링 (5-tuple 기반 자동 차단)
def monitor_suricata_logs():
    # eve.json 이 없으면 로그파일이 없다는 뜻(아무것도 하지 않음)
    if not os.path.exists(EVE_LOG_PATH):
        print(f"[오류] Suricata 로그 파일이 존재하지 않음: {EVE_LOG_PATH}")
        return
    print("[INFO] Suricata alert 로그 감시 시작")

    # eve.json 을 읽어서 실시간으로 로그를 읽음
    with open(EVE_LOG_PATH, "r") as f:

        # 로그 파일의 마지막으로 이동
        f.seek(0, 2)

        # 계속 로그 감지(한 줄씩 읽음)
        while True:
            line = f.readline()

            # 새로운 로그가 없으면 잠시 대기
            if not line:
                time.sleep(0.1)
                continue
            try:
                log = json.loads(line)

                # alert 이벤트만 처리
                if log.get("event_type") == "alert":
                    # 5-tuple 정보 추출(도착지 IP 외에는 필요 X, 좀 더 자세히 보기 위해 가져옴)
                    five_tuple = {
                        "src_ip": log.get("src_ip"),
                        "dst_ip": log.get("dest_ip"),
                        "src_port": log.get("src_port"),
                        "dst_port": log.get("dest_port"),
                        "protocol": log.get("proto")
                    }
                    print("[ALERT] 5-tuple 감지:", five_tuple)

                    # dst_ip 를 출발지로 차단(서버 IP)
                    if five_tuple['dst_ip']:
                        msg = block_ip(five_tuple['dst_ip'])
                        print(f"[ALERT] Suricata 탐지! {five_tuple['dst_ip']} 차단 시도: {msg}")
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"[오류] Suricata 로그 파싱 실패: {e}")

# 프론트엔드 렌더링
@app.route('/')
def index():
    return render_template("index.html")

# 특정 IP 를 차단하고 반환되는 메시지를 return
@app.route('/block', methods=['POST'])
def block():
    ip = request.get_json().get('ip')
    try:
        msg = block_ip(ip)
        return jsonify({"message": msg})
    except Exception as e:
        return jsonify({"message": f"차단 실패: {str(e)}"}), 500

# 특정 IP 를 차단 해제하고 반환되는 메시지를 return
@app.route('/unblock', methods=['POST'])
def unblock():
    ip = request.get_json().get('ip')
    try:
        msg = unblock_ip(ip)
        return jsonify({"message": msg})
    except Exception as e:
        return jsonify({"message": f"해제 실패: {str(e)}"}), 500

# Suricata 실행
@app.route("/start-suricata", methods=["POST"])
def start_suricata():
    try:
        subprocess.Popen([
            "suricata", "-c", "/opt/homebrew/etc/suricata/suricata.yaml", "-i", "192.168.45.238"
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

# 현재 차단된 IP 주소 목록 반환    
@app.route('/blocked-ips', methods=['GET'])
def blocked_ips():
    if not os.path.exists(ANCHOR_FILE):
        return jsonify([])
    with open(ANCHOR_FILE, "r") as f:
        rules = f.readlines()
    
    # "block drop from {ip} to any" 형식에서 ip 만 추출
    ips = []
    for r in rules:
        r = r.strip()
        if r.startswith("block drop from ") and " to any" in r:
            ip = r[len("block drop from "):].split(" to any")[0]
            ips.append(ip)
    return jsonify(ips)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
