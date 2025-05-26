import subprocess
from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import signal
import os
import sys
import time
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from config import INTERFACE, BITMAP_PATH, MONITORING_IP_LIST, SNIFF_LIB, LOG_PATH, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
except ImportError:
    print("config가 설정되지 않았습니다.")
    # Prompt user for interface and IP list at runtime
    from create_config import create_config, prompt_for_ip_and_interface
    INTERFACE, MONITORING_IP_LIST = prompt_for_ip_and_interface()
    print("config.py를 생성했습니다. 다시 실행해주세요.")
    exit(1)


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
    print(f"[INFO] app.py -> get_detected_sessions 호출")
    sniffer.send_detected_sessions()

## 2차 수정본
# 아래의 경로는 환경에 따라 수정해야함
# pf 에서 사용할 앵커 이름 및 경로와 아래에서 사용할 suricata 로그 경로
# /etc/pf.anchors/capstone 에 접근하려면 root 권한이 있어야해서
# 이 코드를 실행할 때 sudo 를 붙여야함
ANCHOR_NAME = "capstone"
ANCHOR_FILE = f"/etc/pf.anchors/{ANCHOR_NAME}"
EVE_LOG_PATH = "/opt/homebrew/var/log/suricata/eve.json"

# Suricata 규칙 파일 경로, YAML 파일 및 SID(고유 식별자)
SURICATA_RULES_PATH = "/opt/homebrew/var/lib/suricata/rules/capstone.rules"
SURICATA_YAML_PATH = "/opt/homebrew/etc/suricata/suricata.yaml"
SID = 1000001  

# 어플리케이션 및 SNI 매핑
# BitTorrent 가 없음
# 또한 몇 개의 어플리케이션을 추가해야할 수 있음
APP_SNI = {
    "youtube": "googlevideo.com",
    "youtube_tls": "googlevideo.com",
    "netflix": ["nflxvideo.net", "nflxso.net", "ftl.netflix.com"],
    "navertv": ["vod.pstatic.net", "smartmediarep.com", "vod.akamaized.net", "livecloud.pstatic.net", "livecloud-thumb.akamaized.net"],
    "wavve": ["vod.cdn.wavve.com", "qvod.cdn.wavve.com", "live.cdn.wavve.com", "flive.cdn.wavve.com"],
    "coupangplay": "coupangstreaming.com",
    "instagram": "fbcdn.net",
    "instagram_tls": "fbcdn.net",
    "steam": ["steambroadcast.akamaized.net", "video-manager.steamstatic.com", "steamcontent.com"],
    "soop": "live.sooplive.co.kr",
}

# 앵커를 pf 에 로드하는 명령
# pfctl -a capstone -f /etc/pf.anchors/capstone : capstone 파일에서 rule 을 읽어와서 PF 에 적용
def reload_anchor():
    result = subprocess.run(["sudo", "pfctl", "-a", ANCHOR_NAME, "-f", ANCHOR_FILE], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(result.stderr)

# 탐지된 ip 주소를 차단하는 rule 을 capstone 파일에 쓰고, pf 에 로드함
def block_ip(src_ip, dst_ip):
    # 출발지 IP, 도착지 IP 에 대한 패킷을 막는 rule
    rule_out = f"block drop from {src_ip} to {dst_ip}\n"
    rule_in = f"block drop from {dst_ip} to {src_ip}\n"

    # capstone 파일이 없으면 오류
    if not os.path.exists(ANCHOR_FILE):
        with open(ANCHOR_FILE, "w") as f:
            f.write("")
    
    # capstone 파일을 읽어서 위에서 설정한 rule 이 이미 있는 지 확인
    with open(ANCHOR_FILE, "r") as f:
        rules = f.readlines()

    already_out = any(rule_out.strip() == r.strip() for r in rules)
    already_in = any(rule_in.strip() == r.strip() for r in rules)

    # 이미 같은 rule 이 있으면 그냥 return
    if already_out and already_in:
        return f"{src_ip} 및 {dst_ip} 는 이미 양방향 차단되어 있습니다."
    
    # 새로운 rule 이라면 capstone 파일에 씀
    with open(ANCHOR_FILE, "a") as f:
        if not already_out:
            f.write(rule_out)
        if not already_in:
            f.write(rule_in)
    
    # 새로 쓴 rule 을 pf 에 로드
    reload_anchor()
    return f"{src_ip} 및 {dst_ip} 양방향 차단 성공"

# 우선 사용하지 않음
# # 입력한 ip 주소 차단 해제함(capstone 에서 해당 rule 을 제거하고, pf 다시 로드)
# def unblock_ip(src_ip, dst_ip):
#     # 출발지 IP, 도착지 IP 에 대한 패킷을 막는 rule
#     rule_out = f"block drop from {src_ip} to {dst_ip}\n"
#     rule_in = f"block drop from {dst_ip} to {src_ip}\n"

#     # 만약 capstone 파일 자체가 없으면 바로 return
#     if not os.path.exists(ANCHOR_FILE):
#         return f"pf anchor file 없음\n"

#     # capstone 파일을 읽어서 해제하려는 rule 을 제외하고 나머지를 new_rules 에 넣음
#     with open(ANCHOR_FILE, "r") as f:
#         rules = f.readlines()

#     # new_rules 를 적음(해제하는 rule 을 제외한 나머지 rule)
#     new_rules = [r for r in rules if rule_in not in r and rule_out not in r]

#     with open(ANCHOR_FILE, "w") as f:
#         f.writelines(new_rules)
    
#     # rule 을 해제한 상태에서 로드
#     reload_anchor()
#     return f"{src_ip} 및 {dst_ip} 양방향 차단 해제 성공"

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

                    # 5-tuple 정보 추출(출발지, 도착지 IP 외에는 필요 X, 좀 더 자세히 보기 위해 가져옴)
                    five_tuple = {
                        "src_ip": log.get("src_ip"),
                        "dst_ip": log.get("dest_ip"),
                        "src_port": log.get("src_port"),
                        "dst_port": log.get("dest_port"),
                        "protocol": log.get("proto")
                    }

                    # suricata 디버깅
                    print("[ALERT] 5-tuple 감지:", five_tuple)

                    # 출발지, 도착지 IP 가 모두 존재하는 경우에만 차단
                    if five_tuple['src_ip'] and five_tuple['dst_ip']:
                        msg = block_ip(five_tuple['src_ip'], five_tuple['dst_ip'])
                        print(f"[ALERT] Suricata 탐지! {five_tuple['dst_ip']} 차단 시도: {msg}")

            except json.JSONDecodeError:
                continue

            except Exception as e:
                print(f"[오류] Suricata 로그 파싱 실패: {e}")

# Suricata가 실행 중인지 확인하는 함수
def is_suricata_running():
    # Suricata 프로세스 확인
    try:
        result = subprocess.run(["pgrep", "suricata"], capture_output=True, text=True)
        print(f"[INFO] Suricata 실행 상태 확인: {result}")

        # 0이면 suricata가 실행 중
        return result.returncode == 0
    
    except Exception as e:
        print(f"Suricata 실행 상태 확인 중 오류 발생: {e}")
        return False

# Suricata 재실행 함수
def restart_suricata():
    try:
        # 실행 중인지 확인
        if is_suricata_running():

            print("[INFO] Suricata가 실행 중입니다. 종료 후 재실행합니다.")

            # 기존 프로세스 종료
            subprocess.run(["pkill", "-f", "suricata"], check=False)

            # 완전히 종료될 때까지 대기
            time.sleep(1)
        else:
            print("[INFO] Suricata가 실행 중이 아닙니다. 새로 실행합니다.")
        
        # Suricata 실행
        subprocess.Popen([
            "suricata", "-c", SURICATA_YAML_PATH, "-i", "en1"
        ])

        t = threading.Thread(target=monitor_suricata_logs, daemon=True)
        t.start()

        print("[INFO] Suricata 실행됨")
        
        # Suricata가 완전히 실행될 때까지 대기
        time.sleep(2) 
        
        # Suricata가 재실행 되었는지 확인
        if is_suricata_running():
            return "Suricata가 성공적으로 재실행되었습니다."
        else:
            return "Suricata 실행에 실패했습니다. 로그를 확인하세요."
        
    except Exception as e:
        return f"Suricata 재실행 실패: {str(e)}"



# Suricata 규칙 추가 함수
def add_suricata_rule(src_ip, dst_ip, app_name):
    # SID 전역 변수
    global SID

    # 규칙을 Suricata 규칙 파일에 추가
    with open(SURICATA_RULES_PATH, "a") as f:

        # 어플리케이션의 모든 SNI 에 대해 규칙 추가
        for sni in APP_SNI[app_name]:
            rule_body_1 = f'(msg:"[ALERT] {app_name} streaming detected"; tls.sni; content:"{sni}"; sid:{SID}; rev:1;)'
            rule_body_2 = f'(msg:"[ALERT] {app_name} streaming detected"; tls.sni; content:"{sni}"; sid:{SID + 1}; rev:1;)'
            rule = f"alert tls {src_ip} any -> any any " + rule_body_1 + "\n" + f"alert tls {dst_ip} any -> any any " + rule_body_2
            
            f.write(rule + "\n")

            print(f"[INFO] Suricata 규칙 추가됨: {rule}")

            # SID 증가
            SID += 2
            print(f"[INFO] SID 증가: {SID}")

# 차단 버튼 클릭 시 실행되는 이벤트
@socketio.on('block_streaming_service') 
def block_packet(data):
    try:

        # socket 으로 받은 패킷 확인
        print(f"[INFO] app.py -> block_packet 호출")
        traffic = data.get('sessions')

        traffic = traffic[0]

        if not traffic:
            print("[INFO] 탐지된 세션이 없습니다.")
            return
            
        print(f"[INFO] 탐지된 세션: {traffic}")
        
        # 세션 정보로 Suricata 재실행 및 규칙 추가
        # for key in traffic:
        src_ip = traffic['src_ip']
        dst_ip = traffic['dst_ip']
        app_name = traffic['predict']
        
        # IP 양방향 차단(현재 클라이언트, 서버 IP 가 각각 무엇인지 알 수 없어서, 양방향 차단)
        msg = block_ip(src_ip, dst_ip)
        # print(f"[BLOCK] 서버 IP 차단: {dst_ip}, 결과: {msg}")
        
        # Suricata 규칙 추가
        add_suricata_rule(src_ip, dst_ip, app_name)
                
        # Suricata 재실행
        restart_result = restart_suricata()
        print(f"[INFO] Suricata 재실행 결과: {restart_result}")
        
    except Exception as e:
        print(f"[ERROR] 세션 처리 중 오류 발생: {str(e)}")

# 모든 IP 차단 해제 함수
@socketio.on('clear_streaming')
def unblock_all_ips():
    print("[DEBUG] clear_streaming 이벤트 수신됨")

    # 만약 capstone 파일 자체가 없으면 바로 return
    if not os.path.exists(ANCHOR_FILE):
        return "차단된 IP가 없습니다."
    
    print(f"[INFO] app.py -> clear_streaming 호출")

    # capstone 파일을 비움 (모든 규칙 제거)
    with open(ANCHOR_FILE, "w") as f:
        f.write("")
    
    print(f"[INFO] capstone 파일 비움")

    # Suricata 규칙 파일을 비움 (모든 규칙 제거)
    with open(SURICATA_RULES_PATH, "w") as f:
        f.write("")
    
    print(f"[INFO] Suricata 규칙 파일 비움")
    
    # 빈 규칙 파일을 pf에 로드 및 suricata 재실행
    reload_anchor()
    restart_suricata()
    return "모든 IP 차단이 해제되었습니다."


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