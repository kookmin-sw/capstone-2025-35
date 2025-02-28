import socket
import json
from ipwhois import IPWhois

JSON_FILE = "monitoring_ip.json"

def get_cidr_from_domain(domain):
    """
    특정 도메인의 CIDR을 RDAP에서 가져오는 함수
    """
    try:
        # 도메인의 IP 가져오기
        ip = socket.gethostbyname(domain)
        print(f"🌐 {domain}의 IP 주소: {ip}")

        # RDAP 기반 CIDR 조회
        obj = IPWhois(ip)
        info = obj.lookup_rdap()
        rdap_cidr = info.get('asn_cidr', None)

        if rdap_cidr:
            print(f"📌 RDAP CIDR: {rdap_cidr}")
            return rdap_cidr
        else:
            print(f"⚠️ RDAP에서 CIDR 정보를 찾을 수 없음: {domain}")
            return None

    except Exception as e:
        print(f"❌ 오류 발생 ({domain}): {e}")
        return None

def save_cidr_to_monitoring(domains):
    """
    여러 도메인의 CIDR 정보를 monitoring_ip.json에 저장하는 함수
    """
    # JSON 파일 로드
    try:
        with open(JSON_FILE, "r") as f:
            monitoring_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        monitoring_data = {"target_application": {}}  # 초기 구조 설정

    # target_application 데이터가 없으면 초기화
    if "target_application" not in monitoring_data:
        monitoring_data["target_application"] = {}

    # 각 도메인의 CIDR 정보 조회 후 추가
    for domain in domains:
        cidr = get_cidr_from_domain(domain)
        if cidr:
            monitoring_data["target_application"][cidr] = domain

    # JSON 파일 저장
    with open(JSON_FILE, "w") as f:
        json.dump(monitoring_data, f, indent=4)

    print(f"✅ CIDR 정보가 {JSON_FILE}에 저장되었습니다!")

# ✅ 사용 예제
save_cidr_to_monitoring(["google.com", "youtube.com", "tv.naver.com", "naver.com"])