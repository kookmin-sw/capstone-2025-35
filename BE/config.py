# config.py
UPDATE_MAC_INTERVAL = 10  # MAC 주소 갱신 주기 (초)
DISC_RANGE = 13  # 이산화 구간
INTERFACE = "en0"  # 네트워크 인터페이스
MONITORING_IP_LIST = ["10.221.97.32"]
MONITORING_PERIOD = 20  # 모니터링 주기 (초)
SNIFF_LIB = "pyshark"
BITMAP_PATH = "bitmap_record.pkl"
LOG_PATH = "../logs"
TARGET_APPLICATIONS = {
    "googlevideo.com" : "youtube",
    "nflxvideo.net" : "netflix",
    "smartmediarep.com": "navertv",
    "naver-vod.pstatic.net": "navertv",
    "vod.cdn.wavve.com": "wavve",
    "vod02-cosmos.coupangstreaming.com": "coupangplay",
    "stream.sooplive.co.kr": "soop",
    "steambroadcast.akamaized.net": "steam",
    "fbcdn.net": "instagram"
}