# config.py
UPDATE_MAC_INTERVAL = 10  # MAC 주소 갱신 주기 (초)
DISC_RANGE = 13  # 이산화 구간
INTERFACE = "en0"  # 네트워크 인터페이스
MONITORING_IP_LIST = ["10.224.121.244"]
MONITORING_PERIOD = 20  # 모니터링 주기 (초)
SNIFF_LIB = "scapy"
BITMAP_PATH = "/Users/minsuhong/Documents/capstone-2025-35/pkl/bitmap_0511_1335.pkl"
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