import os
import subprocess
import time
import random
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# ---------- 설정 ----------
EMAIL = "iamjames77@daum.net"
PASSWORD = "capstone35"
LOOP_COUNT = 5
WAIT_TIME = 10
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
START_TSHARK = True  # True로 변경 시 tshark 실행됨
save_dir = '/home/jang/Documents/new_pcap/capstone-2025-35/pcap/CoupangPlay/PC/WiFi'  # 원하는 pcap 경로로 수정

# ---------- WebDriver 초기화 ----------
options = uc.ChromeOptions()
options.add_argument("--no-first-run")
options.add_argument("--no-service-autorun")
options.add_argument("--password-store=basic")

service = Service(CHROMEDRIVER_PATH)
driver = uc.Chrome(service=service, options=options)

wait = WebDriverWait(driver, WAIT_TIME)
actions = ActionChains(driver)

try:
    # ---------- 로그인 ----------
    driver.get("https://play.coupang.com")
    
    time.sleep(5)
    
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-cy="loginBtn"]'))).click()
    wait = WebDriverWait(driver, 10)
    
    wait.until(EC.presence_of_element_located((By.ID, "login-email-input"))).send_keys(EMAIL)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "login-password-input"))).send_keys(PASSWORD)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button._loginSubmitButton"))).click()

    # 프로필 선택
    time.sleep(3)
    profile_items = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-cy="profileItem"]')))
    random.choice(profile_items).click()

    print("프로필 이미지 클릭")


    # ---------- tshark 실행 (선택) ----------
    if START_TSHARK:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # 전체 파일 이름 경로 생성
        pcap_path = os.path.join(save_dir, f'{timestamp}_Jang_coupangplay.pcap')

        # tshark 실행
        tshark_process = subprocess.Popen(['tshark', '-i', 'wlp61s0', '-w', pcap_path])
        print(f"PCAP 파일 저장 위치: {pcap_path}")
        print("tshark 실행됨")

    # ---------- 콘텐츠 자동 클릭 반복 ----------
    for i in range(LOOP_COUNT):
        print(f"\n--- [{i+1}/{LOOP_COUNT}] 루프 시작 ---")

        driver.get("https://www.coupangplay.com/home")
        wait = WebDriverWait(driver, 10)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="/tv"]'))).click()
        
        wait = WebDriverWait(driver, 10)
        
        time.sleep(3)

        # TV 썸네일 클릭
        thumbnails = wait.until(EC.presence_of_all_elements_located(
            (By.CLASS_NAME, "CarouselSlider_carouselThumbnailContainer__V0qT4")
        ))
        if thumbnails:
            random_thumb = random.choice(thumbnails)
            actions.move_to_element(random_thumb).click().perform()
            print("TV 썸네일 클릭 완료")
        else:
            print("TV 썸네일 요소를 찾지 못했습니다.")
            continue

        # 에피소드 또는 재생 버튼 클릭
        try:
            episode_elements = wait.until(EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "TitleEpisodeBrowser_episodeMargin__tZlnB")
            ))
            if episode_elements:
                episode = random.choice(episode_elements)
                actions.move_to_element(episode).perform()
                episode.click()
                print("에피소드 클릭 완료")
                # 시청 대기
                print("15초 이상 시청 중...")
                time.sleep(20)
        except:
            try:
                play_button = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".TitlePlayCTAButton_shared_ctaContainerRevamped__92_Vs")
                ))
                play_button.click()
                print("재생 버튼 클릭 완료")
                # 시청 대기
                print("15초 이상 시청 중...")
                time.sleep(20)
            except Exception as e:
                print("재생 요소 클릭 실패:", e)


finally:
    print("드라이버 종료")
    driver.quit()
    tshark_process.terminate()  # 정상 종료 요청
    # tshark_process.kill()     # 강제 종료 (terminate가 안 통할 경우)
    tshark_process.wait()       # 종료될 때까지 대기
    print("tshark 캡처 종료")
