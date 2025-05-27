import os
import subprocess
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# 웹드라이버 경로 설정
service = Service('/opt/homebrew/bin/chromedriver')

# Chrome 옵션 설정
options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--headless')  # 필요한 경우 주석 처리

save_dir = '/pcap/chzzk/PC/WiFi'  # 원하는 pcap저장 경로로 수정

# TShark 실행 (필요시 주석 해제)
timestamp = time.strftime("%Y%m%d_%H%M%S")

# 전체 파일 경로 생성
pcap_path = os.path.join(save_dir, f'{timestamp}_MIN_chzzk.pcap') #파일 이름

# tshark 실행
tshark_process = subprocess.Popen(['tshark', '-i', 'en0', '-w', pcap_path])
print(f"PCAP 파일 저장 위치: {pcap_path}")

try:

    for _ in range(5):
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 10)
        driver.get('https://chzzk.naver.com/')
        time.sleep(3)

        try:
            popup_wait = WebDriverWait(driver, 5)  # 팝업만 5초 기다리게 설정
            close_button = popup_wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'loungehome_event_popup_button_close__ftfLQ')))
            close_button.click()
        except Exception:
            print("팝업 닫기 버튼이 없습니다.")
        
        time.sleep(2)

        try:
            live_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/lives']")))
            live_link.click()
        except Exception as e:
            print("라이브 링크를 찾지 못했습니다:", e)
            continue

        # 라이브 페이지 로딩 대기
        time.sleep(5)

        elements = driver.find_elements(By.CLASS_NAME, 'video_card_thumbnail__QXYT8')

        if not elements:
            print("영상 요소를 찾을 수 없습니다.")
            continue

        random_element = random.choice(elements)
        ActionChains(driver).move_to_element(random_element).click().perform()
        print("랜덤 영상 클릭 완료")

        start_time = time.time()

        skip = False

        while time.time() - start_time < 22:
            try:
                skip_button = driver.find_element(By.CLASS_NAME, 'btn_skip')
                ActionChains(driver).move_to_element(skip_button).click().perform()
                print("광고 SKIP 버튼을 클릭했습니다.")
                skip = True
                time.sleep(1)
                break
            except Exception:
                time.sleep(1)

        if(skip == True):
            # 시청 유지 시간
            time.sleep(18)
        else:
            try:
                skip_button = driver.find_element(By.CLASS_NAME, 'btn_skip')
                ActionChains(driver).move_to_element(skip_button).click().perform()
                print("광고 SKIP 버튼을 클릭했습니다.")
                skip == True
            except Exception:
                print("광고 버튼이 없다고 판단합니다")
                time.sleep(1)
            if(skip == True):
                # 시청 유지 시간
                time.sleep(18)

        driver.quit()
        print("시청 완료")
        time.sleep(1)

finally:
    driver.quit()
    tshark_process.terminate()  # 정상 종료 요청
    # tshark_process.kill()     # 강제 종료 (terminate가 안 통할 경우)
    tshark_process.wait()       # 종료될 때까지 대기
    print("드라이버 종료 및 Tshark 종료 완료")
