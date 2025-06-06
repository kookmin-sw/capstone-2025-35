import os
# make_config.py
def create_config():
    INTERFACE = input("Enter the network interface (e.g., en0): ")
    MONITORING_IP_LIST = input("Enter the IP addresses to monitor (comma-separated): ").split(",")

    config_content = f'''import os
# Auto-generated config.py
UPDATE_MAC_INTERVAL = 10  # MAC 주소 갱신 주기 (초)
DISC_RANGE = 13  # 이산화 구간
TARGET_APPLICATIONS = {{
    "googlevideo.com" : "youtube",
    "nflxvideo.net" : "netflix",
    "smartmediarep.com": "navertv",
    "naver-vod.pstatic.net": "navertv",
    "vod.cdn.wavve.com": "wavve",
    "vod02-cosmos.coupangstreaming.com": "coupangplay",
    "fbcdn.net": "instagram",
}}
MONITORING_PERIOD = 20
SNIFF_LIB = "scapy"
BITMAP_PATH = os.path.join(os.path.dirname(__file__), "pkl", "Base.pkl")
LOG_PATH = "../logs"
#DB config
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost:3306/packet_logs_db' # 예시) 'mysql+pymysql://<username>:<password>@<host>:<port>/<database_name>'
SQLALCHEMY_TRACK_MODIFICATIONS = False # 데이터 변경 추적 기능
INTERFACE = "{INTERFACE}"  # 네트워크 인터페이스
MONITORING_IP_LIST = {MONITORING_IP_LIST}  # 모니터링할 IP 주소
'''

    config_path = os.path.join(os.path.dirname(__file__), "config.py")
    with open(config_path, "w") as f:
        f.write(config_content)
    print("config.py has been created successfully.")

def prompt_for_ip_and_interface():
    INTERFACE = input("Enter the network interface (e.g., en0): ")
    MONITORING_IP_LIST = input("Enter the IP addresses to monitor (comma-separated): ").split(",")
    create_config_with_params(INTERFACE, MONITORING_IP_LIST)
    return INTERFACE, MONITORING_IP_LIST

def create_config_with_params(interface, ip_list):
    config_content = f'''import os
# Auto-generated config.py
UPDATE_MAC_INTERVAL = 10  # MAC 주소 갱신 주기 (초)
DISC_RANGE = 13  # 이산화 구간
TARGET_APPLICATIONS = {{
    "googlevideo.com" : "youtube",
    "nflxvideo.net" : "netflix",
    "smartmediarep.com": "navertv",
    "naver-vod.pstatic.net": "navertv",
    "vod.cdn.wavve.com": "wavve",
    "vod02-cosmos.coupangstreaming.com": "coupangplay",
    "fbcdn.net": "instagram",
}}
MONITORING_PERIOD = 20
SNIFF_LIB = "scapy"
BITMAP_PATH = os.path.join(os.path.dirname(__file__), "pkl", "Base.pkl")
LOG_PATH = "../logs"
#DB config
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost:3306/packet_logs_db' # 예시) 'mysql+pymysql://<username>:<password>@<host>:<port>/<database_name>'
SQLALCHEMY_TRACK_MODIFICATIONS = False # 데이터 변경 추적 기능
INTERFACE = "{interface}"  # 네트워크 인터페이스
MONITORING_IP_LIST = {ip_list}  # 모니터링할 IP 주소
'''
    config_path = os.path.join(os.path.dirname(__file__), "config.py")
    with open(config_path, "w") as f:
        f.write(config_content)

if __name__ == "__main__":
    create_config()