import subprocess
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# ChromeDriver 경로 설정
chrome_driver_path = '/usr/local/bin/chromedriver'  # 개인 ChromeDriver 경로로 수정


timestamp = time.strftime("%Y%m%d_%H%M%S")
tshark_process = subprocess.Popen(['tshark', '-i', '개인 네트워크 인터페이스', '-w', f'{timestamp}_파일이름 알아서.pcap'])


# Selenium WebDriver 설정
service = Service(chrome_driver_path)
options = webdriver.ChromeOptions()

# 성능 최적화 옵션 추가
options.add_argument("--incognito")  # 시크릿 모드

#비디오 재생이 느려서 추가한 옵션들
options.add_argument("--no-sandbox")  # 샌드박스 비활성화
options.add_argument("--disable-dev-shm-usage")  # 디바이스 공유 메모리 비활성화
options.add_argument("--disable-software-rasterizer")  # 소프트웨어 렌더링 비활성화
options.add_argument("--disable-blink-features=AutomationControlled")  # 자동화 감지 방지
options.add_argument("--headless") #백그라운드 모드로 실행 만약 어떻게 진행되는지 보고싶으면 이 줄 주석화

# 5번 실행
for _ in range(5):
    # 크롬 드라이버 시작
    driver = webdriver.Chrome(service=service, options=options)

    # YouTube 인기 순위 접속
    driver.get("https://www.youtube.com/feed/trending?")

    # 검색 결과 로딩 대기
    time.sleep(5)  # 페이지 로딩 시간 대기

    # 동영상 링크 찾기 (검색 결과에서 ytd-video-renderer 요소)
    videos = driver.find_elements(By.ID, 'thumbnail')

    # 검색 결과가 없을 경우 예외 처리
    if videos:
        # 랜덤 동영상 선택
        random_video = random.choice(videos)
        print(random_video)
        # 동영상 클릭
        random_video.click()
        # 광고 건너뛰기 대기 및 클릭
        max_wait_time = 16  # 최대 대기 시간 (초)
        start_time = time.time()  # 시작 시간 기록

        skip = False

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
            time.sleep(16)  #광고를 건너뛴 이후부터 

    # 브라우저 종료
    driver.quit()

time.sleep(1)
# tshark 프로세스 종료
tshark_process.terminate()  # tshark 프로세스 종료
print("tshark 프로세스가 종료되었습니다.")

