import argparse
import json
import os

# JSON 파일 경로
json_file = "monitoring_ip.json"

def load_json():
    """JSON 파일을 로드하고, 비어있거나 오류가 있으면 기본값 반환"""
    if os.path.exists(json_file):
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
                return set(data.get("MONITORING_IP", []))
        except (json.JSONDecodeError, ValueError):
            print(f"⚠️ 경고: {json_file} 파일이 비어있거나 손상되었습니다. 기본값을 사용합니다.")
    return set()

def save_json(ips):
    """IP 리스트를 JSON 파일로 저장"""
    with open(json_file, "w") as f:
        json.dump({"MONITORING_IP": sorted(ips)}, f, indent=4)
    print(f"✅ JSON 파일이 업데이트되었습니다! 현재 MONITORING_IP={', '.join(ips)}")

# 기존 데이터 불러오기
existing_ips = load_json()

# Argument Parser 생성
parser = argparse.ArgumentParser(description="MONITORING_IP 관리 스크립트")
parser.add_argument("-i", "--input", type=str, help="추가할 IP 주소 리스트 (쉼표로 구분)")
parser.add_argument("-l", "--list", action="store_true", help="현재 MONITORING_IP 리스트 출력")
args = parser.parse_args()

# -l 옵션: 현재 리스트 출력
if args.list:
    print("📌 현재 MONITORING_IP 리스트:", ", ".join(existing_ips) if existing_ips else "없음")
    exit(0)

# -i 옵션: 새로운 IP 추가
if args.input:
    new_ips = {ip.strip() for ip in args.input.split(",")}
    updated_ips = existing_ips.union(new_ips)  # 중복 제거
    save_json(updated_ips)