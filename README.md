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
python app.py
```