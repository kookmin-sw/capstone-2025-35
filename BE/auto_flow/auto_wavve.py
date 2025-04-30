import os
import subprocess
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# 웹드라이버 설정
service = Service('/usr/local/bin/chromedriver')
options = Options()
options.add_argument("--incognito")
options.add_argument("--headless")  # UI 없이 실행

save_dir = '/home/jang/Documents/new_pcap/capstone-2025-35/pcap/Wavve/PC/WiFi'  # 원하는 pcap 경로로 수정

# TShark 시작
timestamp = time.strftime("%Y%m%d_%H%M%S")
# 전체 파일 경로 생성 이름
pcap_path = os.path.join(save_dir, f'{timestamp}_Jang_wavve.pcap')

# tshark 실행
tshark_process = subprocess.Popen(['tshark', '-i', 'wlp61s0', '-w', pcap_path])
print(f"PCAP 파일 저장 위치: {pcap_path}")
logging.info("TShark 캡처 시작")

try:
    for i in range(5):
        driver = None
        try:
            driver = webdriver.Chrome(service=service, options=options)
            wait = WebDriverWait(driver, 10)
            driver.get('https://www.wavve.com/login')
            logging.info(f"{i+1}회차: 로그인 페이지 접속")

            # 로그인 입력
            username = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="이메일 주소 또는 아이디"]')))
            password = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="비밀번호"]')))
            username.send_keys('daehanmingugulinala@gmail.com')
            password.send_keys('capstone35!')

            login_button = driver.find_element(By.CSS_SELECTOR, 'div.btn-purple.btn-purple-dark a[title="로그인"]')
            login_button.click()
            logging.info(f"{i+1}회차: 로그인 시도")

            time.sleep(3)

            # 프로필 선택
            profiles = driver.find_elements(By.CLASS_NAME, 'user-img')
            if profiles:
                random.choice(profiles).click()
                logging.info(f"{i+1}회차: 랜덤 프로필 선택")
            else:
                logging.warning(f"{i+1}회차: 프로필 없음, 생략")

            time.sleep(3)

            # 팝업 닫기 (있을 경우)
            try:
                close_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'popup-button-close'))
                )
                close_btn.click()
                logging.info(f"{i+1}회차: 팝업 닫기 완료")
            except TimeoutException:
                logging.info(f"{i+1}회차: 팝업 없음")

            time.sleep(2)
            drama_link = driver.find_element(By.XPATH, '//a[contains(text(), "드라마")]')
            drama_link.click()
            time.sleep(5)

            streams = driver.find_elements(By.CSS_SELECTOR, '.thumb.portrait')
            if not streams:
                logging.warning(f"{i+1}회차: 방송 없음")
                continue

            stream = random.choice(streams)
            stream_index = streams.index(stream)
            logging.info(f"{i+1}회차: 방송 썸네일 {stream_index+1}번째 선택")
            driver.execute_script("arguments[0].scrollIntoView();", stream)
            time.sleep(3)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(stream)).click()
            logging.info(f"{i+1}회차: 방송 썸네일 클릭")

            time.sleep(3)

            videos = driver.find_elements(By.CLASS_NAME, 'cell-title')
            if not videos:
                logging.warning(f"{i+1}회차: 영상 항목 없음")
                continue

            video = random.choice(videos)
            video_index = videos.index(video)
            logging.info(f"{i+1}회차: 영상 {video_index+1}번째 선택")
            video.click()
            logging.info(f"{i+1}회차: 영상 선택 및 시청 시작")

            time.sleep(20)
            logging.info(f"{i+1}회차: 영상 시청 완료")

        except Exception as e:
            logging.exception(f"{i+1}회차: 예외 발생 - {e}")

        finally:
            if driver:
                try:
                    driver.quit()
                    logging.info(f"{i+1}회차: 드라이버 종료")
                except Exception as e:
                    logging.warning(f"{i+1}회차: 드라이버 종료 중 오류 - {e}")
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
    logging.info("프로그램 종료")
