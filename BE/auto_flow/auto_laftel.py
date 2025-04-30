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

# 웹드라이버 경로 설정
service = Service('/usr/local/bin/chromedriver')  # 경로 확인

save_dir = '/home/jang/Documents/new_pcap/capstone-2025-35/pcap/laftel/PC/WiFi'  # 원하는 pcap 경로로 수정

# TShark 실행 (현재는 주석 처리)
timestamp = time.strftime("%Y%m%d_%H%M%S")
# 전체 파일 경로 생성 이름
pcap_path = os.path.join(save_dir, f'{timestamp}_Jang_laftel.pcap')

# tshark 실행
tshark_process = subprocess.Popen(['tshark', '-i', 'wlp61s0', '-w', pcap_path])
print(f"PCAP 파일 저장 위치: {pcap_path}")

options = Options()  # ChromeOptions 인스턴스 생성
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--headless")

try:

    driver = webdriver.Chrome(service=service, options=options)
    driver.get('https://laftel.net/auth/login')
    driver.refresh()

    time.sleep(2)

    # 로그인 버튼 클릭
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[span[text()='이메일로 시작']]"))
    ).click()

    time.sleep(2)

    # 이메일 입력 필드
    email_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"][placeholder="이메일을 입력해주세요"]'))
    )
    email_input.send_keys("daehanmingugulinala@gmail.com")

    time.sleep(2)

    # '다음' 버튼 클릭
    next_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//button[text()="다음"]'))
    )
    next_button.click()

    # 비밀번호 입력 필드
    password_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"][placeholder="비밀번호를 입력해주세요"]'))
    )
    password_input.send_keys("capstone35!")

    time.sleep(2)

    # 로그인 버튼 클릭
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//button[text()="로그인"]'))
    )
    login_button.click()

    time.sleep(2)

    # 프로필 선택
    items = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-cy="profile-item"]'))
    )
    if items:
        random.choice(items).click()
    else:
        print("프로필 선택 실패")

    time.sleep(5)

    for i in range(5):

        # SVG 아이콘 찾기 (클래스명 기준)
        svg_element = driver.find_element(By.CSS_SELECTOR, '.sc-93bcca8-5.klLwFd')

        # 클릭
        svg_element.click()

        time.sleep(4)

        # <a> 태그 요소 찾기 (클래스명을 사용하여)
        link = driver.find_element(By.CSS_SELECTOR, '.sc-a4352714-11.capRUh')

        # 클릭
        link.click()

        time.sleep(4)

        # 'sc-ed8262e4-0 jgcDvs' 클래스를 가진 모든 요소 찾기
        elements = driver.find_elements(By.CSS_SELECTOR, '.sc-ed8262e4-0.jgcDvs')

        # 요소가 존재하면 랜덤으로 클릭
        if elements:
            random_element = random.choice(elements)  # 랜덤으로 요소 선택
            random_element.click()
            print("요소를 클릭했습니다.")
        else:
            print("대상 요소를 찾을 수 없습니다.")

        time.sleep(3)

        # 'sc-472bf40-2 kRUErM' 클래스의 영상 선택
        elements = driver.find_elements(By.CSS_SELECTOR, '.sc-472bf40-2.kRUErM')
        if elements:
            random.choice(elements).click()
            print("영상 시청 시작")
        else:
            print("대상 영상 요소를 찾을 수 없습니다.")

        time.sleep(20)

        # 링크 클릭 (SVG 아이콘을 포함한 <a> 태그)
        link = driver.find_element(By.CSS_SELECTOR, 'a[href="/"]')
        link.click()

        time.sleep(5)

except Exception as e:
    print("오류 발생:", e)

finally:
    # 마지막 드라이버 종료
    print("크롬 드라이버 종료")
    driver.quit()
    # TShark 종료 (주석 처리됨)
    tshark_process.terminate()  # 정상 종료 요청
    # tshark_process.kill()     # 강제 종료 (terminate가 안 통할 경우)
    tshark_process.wait()       # 종료될 때까지 대기
    print("프로그램 종료")
