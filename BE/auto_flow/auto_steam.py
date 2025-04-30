import os
import subprocess
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

# 로그 설정
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Chrome WebDriver 설정
service = Service('/usr/local/bin/chromedriver')
options = Options()
options.add_argument("--incognito")
options.add_argument("--headless")  # UI 없이 백그라운드 실행

save_dir = '/home/jang/Documents/new_pcap/capstone-2025-35/pcap/Steam/PC/WiFi'  # 원하는 pcap 경로로 수정

# TShark 시작
timestamp = time.strftime("%Y%m%d_%H%M%S")
# 전체 파일 경로 생성 이름
pcap_path = os.path.join(save_dir, f'{timestamp}_Jang_steam.pcap')

# tshark 실행
tshark_process = subprocess.Popen(['tshark', '-i', 'wlp61s0', '-w', pcap_path])
print(f"PCAP 파일 저장 위치: {pcap_path}")
logging.info("TShark 캡처 시작")

driver = None

try:
    for i in range(5):  # 5번 반복
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.get('https://steamcommunity.com/?subsection=broadcasts')
            logging.info(f"{i+1}회차: 방송 페이지 접속")

            time.sleep(5)  # 페이지 로딩 대기

            # 스크롤 3회
            for _ in range(3):
                driver.execute_script("window.scrollBy(0, 2000);")
                time.sleep(3)

            # 방송 목록 수집
            streams = driver.find_elements(By.CLASS_NAME, 'apphub_CardContentClickable')
            if not streams:
                logging.warning(f"{i+1}회차: 방송 목록이 비어 있음. 다음으로 넘어갑니다.")
                driver.quit()
                continue

            random_stream = random.choice(streams)
            index = streams.index(random_stream)
            logging.info(f"{i+1}회차: 선택된 방송 인덱스 = {index}")

            # 클릭 시도
            try:
                random_stream.click()
                logging.info(f"{i+1}회차: 방송 클릭 성공")
            except WebDriverException as e:
                logging.error(f"{i+1}회차: 방송 클릭 실패 - {e}")
                driver.quit()
                continue

            time.sleep(20)  # 방송 시청
            logging.info(f"{i+1}회차: 방송 시청 완료")

        except Exception as e:
            logging.exception(f"{i+1}회차: 오류 발생 - {e}")

        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            time.sleep(1)

except Exception as main_e:
    logging.exception(f"전체 반복 중 오류 발생: {main_e}")

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
