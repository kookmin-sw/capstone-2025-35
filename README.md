# 1. 환경설정
conda 혹은 pyenv를 활용하여 파이썬 버전을 맞춰주세요
```bash
conda create -n appdetect python=3.12

conda activate appdetect
git clone https://github.com/kookmin-sw/capstone-2025-35.git
cd capstone-2025-35
pip install -r requirements.txt
```
# 2. 감시할 IP 추가
```bash
cd BE
#모니터링할 IP 추가
python create_ip_json.py -i PUT.YOUR.MONITORING.IP1,PUT.YOUR.MONITORING.IP2
#python create_ip_json.py -l로 IP 리스트를 확인할 수 있습니다.
#Linux sniff 때문에 root 권한 필요
sudo $(which python) app.py
#macOS
python app.py
```
# 3. 운영체제 별 app.py 실행
## macOS
```bash
sudo python app.py
```
## Linux
```bash
#Linux의 경우 flask_socketio 실행하기 위하여 root 권한 필요
sudo $(which python) app.py
```

# to_df를 사용하기 전 설정
## pcap 파일 이름 규칙
pcap 파일 이름을 다음과 같이 해주세요. 
민수홍: MIN_01.pcap
박도현: PARK_01.pcap
서동현: SEO_01.pcap
장승훈: JANG_01.pcap
전홍선: JEON_01.pcap
어플리케이션/기기 종류/인터넷 종류에 따라 폴더를 생성할 것이기 때문에 **성과 순서**만 파일 이름에 저장해주세요
## pcap 폴더 구조
```bash
pcap/                            # 원본 PCAP 파일 저장 폴더
│── YouTube/                     # 어플리케이션 이름
│   ├── Phone/                   # 기기 종류
│   │   ├── WiFi/                # 인터넷 종류
│   │       ├── MIN_01.pcap
│   │       ├── MIN_02.pcap
│   │   
│   ├── PC/                      # 기기 종류
│       ├── WiFi/                # 인터넷 종류
│       │   ├── MIN_01.pcap
│       │   ├── MIN_02.pcap
│       ├── Ethernet/
│           ├── MIN_01.pcap
│           ├── MIN_02.pcap
```
## 명령어
```bash
python to_df.py
```
## 결과
```bash
csv/                              # 변환된 CSV 파일 저장 폴더
│── YouTube/                      # 어플리케이션 이름
│   ├── Phone/                    # 기기 종류
│   │   ├── WiFi/                 # 인터넷 종류
│   │       ├── MIN_01.csv
│   │       ├── MIN_02.csv
│   │ 
│   ├── PC/                       # 기기 종류
│       ├── WiFi/
│       │   ├── MIN_01.csv
│       │   ├── MIN_02.csv
│       ├── Ethernet/
│           ├── MIN_01.csv
│           ├── MIN_02.csv
```

# 데이터셋 현황 (자기이름 넣어서 업데이트 해주세요)
데이터셋 현황 변경은 시에만 master로 push 부탁드립니다
데이터셋 csv를 올리는 경우 csv 브랜치로 push 해주세요
## 민수홍
### 유튜브
MacOS Wi-Fi(학교): 5
### 네이버 TV
MacOS Wi-Fi(학교): 5
### 쿠팡플레이
MacOS Wi-Fi(학교): 5
### 넷플릭스
MacOS Wi-Fi(학교): 5