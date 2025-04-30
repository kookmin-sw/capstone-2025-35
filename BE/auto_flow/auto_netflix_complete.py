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
service = Service('/usr/local/bin/chromedriver')  # 경로 확인

save_dir = '/home/jang/Documents/new_pcap/capstone-2025-35/pcap/NetFlix/PC/WiFi'  # 원하는 pcap 경로로 수정

# TShark 실행
timestamp = time.strftime("%Y%m%d_%H%M%S")
# 전체 파일 경로 생성 이름
pcap_path = os.path.join(save_dir, f'{timestamp}_Jang_netflix.pcap')

# tshark 실행
tshark_process = subprocess.Popen(['tshark', '-i', 'wlp61s0', '-w', pcap_path])
print(f"PCAP 파일 저장 위치: {pcap_path}")
options = Options()  # ChromeOptions 인스턴스 생성
options.add_argument("--incognito")  # 시크릿 모드 활성화
options.add_argument("--disable-extensions")  # 확장 프로그램 비활성화
options.add_argument("--disable-gpu")  # GPU 비활성화
driver = None

try:
    driver = webdriver.Chrome(service=service, options=options)  # 새로운 드라이버 인스턴스 생성
    driver.get('https://www.netflix.com/kr/login')  # 로그인 페이지 URL
    wait = WebDriverWait(driver, 10)

    # 로그인
    wait.until(EC.presence_of_element_located((By.NAME, 'userLoginId'))).send_keys('iamjames@naver.com')
    wait.until(EC.presence_of_element_located((By.NAME, 'password'))).send_keys('capstone35')
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-uia="sign-in-button"]'))).click()
    time.sleep(3)

    # 프로필 선택
    try:
        profile_links = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'profile-link')))
        random.choice(profile_links).click()
        time.sleep(3)
    except:
        print("프로필 선택 실패 또는 생략")

    for i in range(5):

        #꼭 있어야 하는 요소
        actions = ActionChains(driver)
        actions.move_to_element(driver.find_element(By.TAG_NAME, 'body')).perform()

        time.sleep(5)


        # 영상 라인 필터링
        all_lines = driver.find_elements(By.CSS_SELECTOR, '.lolomoRow.lolomoRow_title_card.ltr-0')
        visible_lines = [line for line in all_lines if 'mobile-games-row' not in line.get_attribute('class')]

        if not visible_lines:
            print(f"{i+1}회차: 재생 가능한 라인이 없습니다.")
            continue

        selected_line = random.choice(visible_lines)
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", selected_line)
        time.sleep(3)


        cards = selected_line.find_elements(By.CSS_SELECTOR, '.title-card-container.ltr-0')
        if not cards:
            print(f"{i+1}회차: 영상 썸네일이 없습니다.")
            continue
        selected_card = random.choice(cards[:4])
        time.sleep(2)
        try:
            selected_card.click()
            print(f"{i+1}회차: 영상 썸네일 클릭")
        except Exception as e:
            print(f"{i+1}회차: 썸네일 클릭 실패 - {e}")
            continue
        time.sleep(3)
        # 영상 재생 시작
        try:
            play_button = wait.until(EC.element_to_be_clickable((
                By.XPATH, "//*[contains(@class, 'previewModal--player-titleTreatmentWrapper')]"
            )))
            play_button.click()
            print(f"{i+1}회차: 영상 재생 시작")
        except Exception as e:
            print(f"{i+1}회차: 영상 재생 실패 - {e}")
            continue

        time.sleep(20)
        print(f"{i+1}회차: 영상 시청 완료")

        # 다음 영상 위해 browse 페이지로 복귀
        driver.get('https://www.netflix.com/browse')
        time.sleep(2)
except Exception as e:
    print("전체 예외 발생:", e)

finally:
    if driver:
        driver.quit()
        print("드라이버 종료 완료")

    if tshark_process.poll() is None:
        tshark_process.terminate()
        try:
            tshark_process.wait(timeout=5)
            print("TShark 정상 종료")
        except subprocess.TimeoutExpired:
            tshark_process.kill()
            print("TShark 강제 종료")

    print("프로그램 종료")
