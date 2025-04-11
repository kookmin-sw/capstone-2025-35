import subprocess
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# 웹드라이버 경로 설정
service = Service('/usr/local/bin/chromedriver')  # 개인 크롬 드라이버경로 확인

options = Options()  # ChromeOptions 인스턴스 생성
options.add_argument("--incognito")  # 시크릿 모드 활성화
options.add_argument("--headless") #백그라운드 모드로 실행 만약 어떻게 진행되는지 보고싶으면 이 줄 주석화

# TShark 실행
timestamp = time.strftime("%Y%m%d_%H%M%S") #시간별 저장
tshark_process = subprocess.Popen(['tshark', '-i', '개인 네트워크 인터페이스', '-w', f'{timestamp}_파일이름.pcap'])


for _ in range(5):
    driver = webdriver.Chrome(service=service, options=options)

    # Soop 사이트로 이동
    driver.get('https://www.sooplive.co.kr/live/all')

    time.sleep(2)

    # 랜덤 비디오 클릭
    videos = driver.find_elements(By.CLASS_NAME, "thumbs-box")
    random_video = random.choice(videos)
    random_video.click()

    time.sleep(21) #로딩 시간 + 동영상 시청 15초

    driver.quit()

    time.sleep(1)

# 드라이버 종료 (마지막 드라이버 인스턴스)
driver.quit()
# TShark 종료
time.sleep(1)
tshark_process.terminate()

