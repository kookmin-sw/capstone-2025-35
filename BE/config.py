# config.py
UPDATE_MAC_INTERVAL = 10  # MAC 주소 갱신 주기 (초)
DISC_RANGE = 13  # 이산화 구간
# INTERFACE = "wlp61s0"  # 네트워크 인터페이스
INTERFACE = "en0"  # 네트워크 인터페이스
# MONITORING_IP_LIST = ["192.168.0.29"]
MONITORING_IP_LIST = ["192.168.45.212"]
MONITORING_PERIOD = 20  # 모니터링 주기 (초)
SNIFF_LIB = "scapy"
# BITMAP_PATH = "/home/jang/Documents/capstone-2025-35/pkl/bitmap_0511_1335.pkl"
BITMAP_PATH = "/Users/seodonghyun/Desktop/국민대 수업자료(현재)/4-1/캡스톤/capstone-2025-35/pkl/bitmap_0511_1335.pkl"
LOG_PATH = "../logs"
TARGET_APPLICATIONS = {
    "googlevideo.com" : "youtube",
    "nflxvideo.net" : "netflix",
    "smartmediarep.com": "navertv",
    "naver-vod.pstatic.net": "navertv",
    "vod.cdn.wavve.com": "wavve",
    "vod02-cosmos.coupangstreaming.com": "coupangplay",
    "fbcdn.net": "instagram",
}