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
service = Service('/usr/local/bin/chromedriver')  # 개인 크롬 드라이버 경로 확인

# TShark 실행
timestamp = time.strftime("%Y%m%d_%H%M%S")
tshark_process = subprocess.Popen(['tshark', '-i', 'wlp61s0', '-w', f'{timestamp}_Linux_Jang_wavve.pcap'])

options = Options()  # ChromeOptions 인스턴스 생성
options.add_argument("--incognito")  # 시크릿 모드 활성화
options.add_argument("--headless") #백그라운드 모드로 실행 만약 어떻게 진행되는지 보고싶으면 이 줄 주석화

try:

    for _ in range(5):
        driver = webdriver.Chrome(service=service, options=options)  # 새로운 드라이버 인스턴스 생성

        # wavve 로그인 페이지로 이동
        driver.get('https://www.wavve.com/login')  # 로그인 페이지 URL

        # 로그인 정보 입력 (아이디와 비밀번호)
        username = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="이메일 주소 또는 아이디"]')))  # 아이디 입력 필드
        password = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="비밀번호"]')))  # 비밀번호 입력 필드

        username.send_keys('daehanmingugulinala@gmail.com')  # 여기에 사용자 아이디 입력
        password.send_keys('capstone35!')  # 여기에 사용자 비밀번호 입력

        # 로그인 버튼 클릭
        login_button = driver.find_element(By.CSS_SELECTOR, 'div.btn-purple.btn-purple-dark a[title="로그인"]')  # 로그인 버튼의 CSS 선택자
        login_button.click()

        time.sleep(3)  # 로그인 후 페이지 로딩 대기

        #프로필 선택 코드 만들기
        profile_links = driver.find_elements(By.CLASS_NAME, 'user-img')  # 모든 프로필 링크 요소 찾기
        if profile_links:  # 요소가 존재하는지 확인
            random_profile = random.choice(profile_links)  # 랜덤으로 선택
            random_profile.click()  # 랜덤으로 선택된 프로필 클릭
        
        time.sleep(3)

        # 팝업 닫기 버튼이 있는 경우 클릭
        try:
            close_button = WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.CLASS_NAME, 'popup-button-close')))  # 팝업 닫기 버튼 
            close_button.click()  # 팝업 닫기 버튼 클릭
        except Exception as e:
            print("팝업 닫기 버튼이 없습니다")

        time.sleep(3)

        streams = driver.find_elements(By.CLASS_NAME, 'badge-list')
    
        # 방송 목록이 비어 있는지 확인
        if not streams:
            print("방송 목록이 비어 있습니다. 다시 시도해 주세요.")
        else:
            random_stream = random.choice(streams)

            # random_stream 요소가 화면에 보이도록 스크롤  지우면 클릭 가능 상태가 불가
            driver.execute_script("arguments[0].scrollIntoView();", random_stream)
            
            time.sleep(3)
            # badge-list 요소 클릭 가능할 때까지 대기
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(random_stream))  # 클릭 가능 여부 확인
            random_stream.click() 

            time.sleep(3) 

            video = driver.find_elements(By.CLASS_NAME, 'cell-title')

            random_video = random.choice(video)

            random_video.click()

            time.sleep(20)

            driver.quit()
finally:
    # 드라이버 종료 (마지막 드라이버 인스턴스)
    driver.quit()
    # TShark 종료
    time.sleep(1)
    tshark_process.terminate()

