import os
import subprocess
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, WebDriverException

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# ChromeDriver 경로
chrome_driver_path = '/usr/local/bin/chromedriver'

save_dir = '/home/jang/Documents/new_pcap/capstone-2025-35/pcap/youtube/PC/WiFi'  # 원하는 pcap 경로로 수정

# TShark 실행
timestamp = time.strftime("%Y%m%d_%H%M%S")
# 전체 파일 경로 생성 이름
pcap_path = os.path.join(save_dir, f'{timestamp}_Jang_youtube.pcap')

# tshark 실행
tshark_process = subprocess.Popen(['tshark', '-i', 'wlp61s0', '-w', pcap_path])
print(f"PCAP 파일 저장 위치: {pcap_path}")
logging.info("TShark 캡처 시작")

# WebDriver 옵션
options = Options()
options.add_argument("--incognito")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--headless")

service = Service(chrome_driver_path)

try:
    for i in range(5):
        driver = None
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.get("https://www.youtube.com/feed/trending")
            logging.info(f"{i+1}회차: YouTube 인기 영상 페이지 접속")
            time.sleep(5)

            # 썸네일 요소들 찾기
            videos = driver.find_elements(By.ID, 'thumbnail')
            if not videos:
                logging.warning(f"{i+1}회차: 영상 목록 없음")
                continue

            video = random.choice(videos)
            video_index = videos.index(video)
            logging.info(f"{i+1}회차: {video_index + 1}번째 영상 선택")
            time.sleep(1)
            video.click()

            # 광고 건너뛰기 대기
            logging.info(f"{i+1}회차: 광고 탐색 중")
            max_wait_time = 16
            start_time = time.time()
            ad_skipped = False

            while True:
                try:
                    # 광고 건너뛰기 버튼 찾기
                    skip_ad_button = driver.find_element(By.CLASS_NAME, 'ytp-skip-ad-button')
                    skip_ad_button.click()  # 광고 건너뛰기 버튼 클릭
                    print("광고를 건너뛰었습니다.")
                    skip = True
                    break  # 클릭 후 while 문 종료
                except Exception as e:
                    # 광고 건너뛰기 버튼을 찾지 못한 경우
                    pass
                
                # 최대 대기 시간 초과 시 종료
                if time.time() - start_time > max_wait_time:
                    print("광고가 아니거나 광고 스킵버튼이 아닌 경우")
                    break
                
                time.sleep(1)  # 1초 대기 후 다시 시도

            if(skip == True):
                time.sleep(17)  #광고를 건너뛴 이후부터 

        except WebDriverException as e:
            logging.error(f"{i+1}회차: 드라이버 오류 발생: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                    logging.info(f"{i+1}회차: 드라이버 종료")
                except Exception as e:
                    logging.warning(f"{i+1}회차: 드라이버 종료 실패: {e}")
            time.sleep(1)

finally:
    logging.info("TShark 종료 시도")
    if tshark_process.poll() is None:
        tshark_process.terminate()
        try:
            tshark_process.wait(timeout=5)
            logging.info("TShark 정상 종료")
        except subprocess.TimeoutExpired:
            tshark_process.kill()
            logging.warning("TShark 강제 종료됨")
    logging.info("프로그램 종료 완료")
