import subprocess
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC

# 웹드라이버 경로 설정
service = Service('/usr/local/bin/chromedriver')  # Chrome 드라이버 설치 경로 (이건 개인마다 알아서 지정)
options = Options()  # ChromeOptions 인스턴스 생성

options.add_argument("--headless") #백그라운드 모드로 실행 만약 어떻게 진행되는지 보고싶으면 이 줄 주석화


# TShark 실행
timestamp = time.strftime("%Y%m%d_%H%M%S")
tshark_process = subprocess.Popen(['tshark', '-i', 'wlp61s0', '-w', f'{timestamp}_Linux_Jang_naver.pcap'])

for _ in range(5):

    driver = webdriver.Chrome(service=service,options=options)  # 새로운 드라이버 인스턴스 생성

    driver.get("https://tv.naver.com/")

    time.sleep(3) #페이지 로딩이 완료될 시간

    # "영상 더보기" 버튼 클릭
    more_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.index_button_more__dyGvw')))  # 영상 더보기 버튼 찾기
    more_button.click()  # 버튼 클릭

    time.sleep(3)#페이지 로딩이 완료될 시간

    # 비디오 요소를 기다리고 찾기
    video_elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.Top100ClipCard_preview_area__beCkv')))  # Top100ClipCard_preview_area__beCkv 요소 찾기
    #print(len(video_elements)) #총 100개의 영상이므로 100이 출력

    if video_elements:  # 요소가 존재하는지 확인
        random_video = random.choice(video_elements)  # 랜덤으로 선택
        random_video.click() 

        max_wait_time = 17  # 최대 대기 시간 (초) 최대 광고 길이 15초
        start_time = time.time()  # 시작 시간 기록
        skip = False

        while True:
            try:
                # 광고 건너뛰기 버튼 찾기
                skip_ad_button = driver.find_element(By.CLASS_NAME, 'btn_skip')
                skip_ad_button.click()  # 광고 건너뛰기 버튼 클릭
                print("광고를 건너뛰었습니다.")
                skip = True
                break  # 클릭 후 while 문 종료
            except Exception as e:
                # 광고 건너뛰기 버튼을 찾지 못한 경우
                pass
            
            # 최대 대기 시간 초과 시 종료
            if time.time() - start_time > max_wait_time:
                print("광고가 없는 영상입니다.")
                time.sleep(2)
                break
            
            time.sleep(1)  # 1초 대기 후 다시 시도

        if(skip == True):
            time.sleep(16)  # 광고 skip 완료 후 15초 정도 시청하기 위한 용도 아니면 광고가 없었단 뜻이므로 이미 영상 시청 완료

        driver.quit()  # Chrome 브라우저 종료

time.sleep(2)
tshark_process.terminate()




