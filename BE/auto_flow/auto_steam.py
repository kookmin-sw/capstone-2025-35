import subprocess
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# 웹드라이버 경로 설정
service = Service('/usr/local/bin/chromedriver')  # 개인 크롬 드라이버 지정
options = Options()  # ChromeOptions 인스턴스 생성
options.add_argument("--incognito")  # 시크릿 모드 활성화
options.add_argument("--headless") #백그라운드 모드로 실행 만약 어떻게 진행되는지 보고싶으면 이 줄 주석화

# TShark 실행
timestamp = time.strftime("%Y%m%d_%H%M%S")
tshark_process = subprocess.Popen(['tshark', '-i', '개인 네트워크 인터페이스', '-w', f'{timestamp}_steam.pcap'])

try:
    for _ in range(5):  # 총 5번 반복
        driver = webdriver.Chrome(service=service, options=options)  # 새로운 드라이버 인스턴스 생성

        # 방송 페이지로 이동
        driver.get('https://steamcommunity.com/?subsection=broadcasts')

        time.sleep(5)  # 페이지 로딩 대기

        # 페이지 스크롤을 아래로 이동 (예: 100 * _ 픽셀) 더 많은 동영상 선택지를 부여하기 위해 필요
        driver.execute_script(f"window.scrollBy(0, {2000 });")
        time.sleep(3)  # 스크롤 후 잠시 대기

        # 페이지 스크롤을 아래로 이동 (예: 100 * _ 픽셀)
        driver.execute_script(f"window.scrollBy(0, {2000 });")
        time.sleep(3)  # 스크롤 후 잠시 대기

        # 페이지 스크롤을 아래로 이동 (예: 100 * _ 픽셀)
        driver.execute_script(f"window.scrollBy(0, {2000 });")
        time.sleep(4)  # 스크롤 후 잠시 대기

        # 방송 목록 가져오기
        streams = driver.find_elements(By.CLASS_NAME, 'apphub_CardContentClickable')

        # 방송 목록이 비어 있는지 확인
        if not streams:
            print("방송 목록이 비어 있습니다. 다시 시도해 주세요.")
            break  # 방송 목록이 비어 있으면 반복 종료
        else:
            # 방송 목록에서 랜덤으로 선택
            random_stream = random.choice(streams)

            # 선택한 방송의 인덱스 출력
            #num = streams.index(random_stream)
            #print(f"선택한 방송의 인덱스: {num}")

            # 선택한 방송 클릭
            random_stream.click()

            time.sleep(20)  # 방송 15초 이상 시청 컴마다 로딩 되는 시간이 다를 수 있기 때문에 알아서 지정

        driver.quit()  # 드라이버 종료

finally:
    # 드라이버 종료 (마지막 드라이버 인스턴스)
    driver.quit()
    # TShark 종료
    time.sleep(1)
    tshark_process.terminate()

#페이지 번호 랜덤 넣기
