import os
import subprocess
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchElementException

# 로그 설정
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# 웹드라이버 경로 설정
service = Service('/usr/local/bin/chromedriver')

options = Options()
options.add_argument("--incognito")
options.add_argument("--headless")  # 백그라운드 실행

save_dir = '/home/jang/Documents/new_pcap/capstone-2025-35/pcap/soop/PC/WiFi'  # 원하는 pcap 경로로 수정

# TShark 시작
timestamp = time.strftime("%Y%m%d_%H%M%S")
# 전체 파일 경로 생성 이름
pcap_path = os.path.join(save_dir, f'{timestamp}_Jang_soop.pcap')

# tshark 실행
tshark_process = subprocess.Popen(['tshark', '-i', 'wlp61s0', '-w', pcap_path])
print(f"PCAP 파일 저장 위치: {pcap_path}")
logging.info("TShark 캡처 시작")

try:
    for i in range(5):
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.get('https://www.sooplive.co.kr/live/all')
            time.sleep(2)

            videos = driver.find_elements(By.CLASS_NAME, "thumbs-box")
            if not videos:
                logging.warning(f"{i+1}회차: 영상 리스트 없음")
                driver.quit()
                continue

            random_video = random.choice(videos)
            logging.info(f"{i+1}회차: 랜덤 Soop 영상 클릭")
            try:
                random_video.click()
            except WebDriverException as click_error:
                logging.error(f"{i+1}회차: 클릭 실패 - {click_error}")
                driver.quit()
                continue

            time.sleep(21)  # 로딩 + 시청 시간
            logging.info(f"{i+1}회차: 영상 시청 완료")

        except Exception as inner_e:
            logging.exception(f"{i+1}회차: 오류 발생 - {inner_e}")
        finally:
            try:
                driver.quit()
            except:
                pass
            time.sleep(1)

except Exception as e:
    logging.exception("전체 실행 중 오류 발생: %s", e)

finally:
    if tshark_process and tshark_process.poll() is None:
        logging.info("TShark 종료 중...")
        tshark_process.terminate()
        try:
            tshark_process.wait(timeout=5)
            logging.info("TShark 정상 종료")
        except subprocess.TimeoutExpired:
            tshark_process.kill()
            logging.warning("TShark 강제 종료됨")

    logging.info("프로그램 종료")

