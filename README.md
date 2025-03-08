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

# to_df 사용법
```bash
python to_df.py -p pcap\application_name # pcap을 저장하는 pcap\application_name에 저장하길 권장
```
csv\application_name에 csv파일이 저장됨