# config.py
UPDATE_MAC_INTERVAL = 10  # MAC 주소 갱신 주기 (초)
DISC_RANGE = 13  # 이산화 구간
INTERFACE = "en0"  # 네트워크 인터페이스
MONITORING_IP_LIST = [""] # 추적하고 싶은 노트북과 연결된 와이파이의 IP작성 
MONITORING_PERIOD = 20  # 모니터링 주기 (초)
SNIFF_LIB = "scapy"
BITMAP_PATH = "/Users/dh_park/Desktop/CAPSTONE/capstone-2025-35/pkl/bitmap_0515_1607.pkl"
LOG_PATH = "../logs"
TARGET_APPLICATIONS = {
    "googlevideo.com" : "youtube",
    "nflxvideo.net" : "netflix",
    "smartmediarep.com": "navertv",
    "naver-vod.pstatic.net": "navertv",
    "vod.cdn.wavve.com": "wavve",
    "vod02-cosmos.coupangstreaming.com": "coupangplay",
    "fbcdn.net": "instagram",
    "pc-web.stream.sooplive.co.kr": "soop",

}
#DB config
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost:3306/packet_logs_db' # 예시) 'mysql+pymysql://<username>:<password>@<host>:<port>/<database_name>'
SQLALCHEMY_TRACK_MODIFICATIONS = False # 데이터 변경 추적 기능