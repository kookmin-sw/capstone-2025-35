import subprocess
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 웹드라이버 경로 설정
# service = Service('/usr/local/bin/chromedriver')  # 개인 크롬 드라이버경로 확인
service = Service(ChromeDriverManager().install())

options = Options()  # ChromeOptions 인스턴스 생성
options.add_argument("--incognito")  # 시크릿 모드 활성화
# options.add_argument("--headless") #백그라운드 모드로 실행 만약 어떻게 진행되는지 보고싶으면 이 줄 주석화

# TShark 실행
timestamp = time.strftime("%Y%m%d_%H%M%S") #시간별 저장
tshark_process = subprocess.Popen(['tshark', '-i', 'en0', '-w', f'{timestamp}_macos_Park_twitch.pcap'])


for _ in range(5):
    driver = webdriver.Chrome(service=service, options=options)

    # Soop 사이트로 이동
    driver.get('https://www.twitch.tv/')

    # time.sleep(10)

    # 랜덤 비디오 클릭
    wait = WebDriverWait(driver, 10)
    videos = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//a[contains(@class, "side-nav-card") and contains(@class, "tw-link")]')))
    random_video = random.choice(videos)
    random_video.click()

    time.sleep(3)

    buttons = driver.find_elements(By.XPATH, '//div[@data-a-target="tw-core-button-label-text" and text()="시청 시작"]')
    if buttons:
        button = buttons[0]  # 첫 번째 버튼 가져오기
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)  # 화면 가운데로 스크롤
        button.click()

    time.sleep(20) #로딩 시간 + 동영상 시청 15초

    driver.quit()

    time.sleep(1)

# 드라이버 종료 (마지막 드라이버 인스턴스)
driver.quit()
# TShark 종료
time.sleep(1)
tshark_process.terminate()

