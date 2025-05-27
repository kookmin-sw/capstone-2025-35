import os
import subprocess
import time
import logging
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

save_dir = '/home/jang/Documents/new_pcap/capstone-2025-35/pcap/instagram/PC/WiFi'  # 원하는 pcap 경로로 수정

# ChromeDriver 및 TShark 설정
chrome_driver_path = '/usr/local/bin/chromedriver'
timestamp = time.strftime("%Y%m%d_%H%M%S")

# 전체 파일 경로 생성 이름
pcap_path = os.path.join(save_dir, f'{timestamp}_Jang_instagram.pcap')

# tshark 실행
tshark_process = subprocess.Popen(['tshark', '-i', 'wlp61s0', '-w', pcap_path])
print(f"PCAP 파일 저장 위치: {pcap_path}")
logging.info("TShark 캡처 시작")

# Selenium 옵션
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--headless")  # 필요 시 활성화

driver = None

try:
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
    driver.get('https://www.instagram.com/#')
    logging.info("Instagram 로그인 페이지 접속")

    time.sleep(2)

    # 로그인 입력
    driver.find_element(By.NAME, "username").send_keys("개인 이메일")
    time.sleep(1)
    driver.find_element(By.NAME, "password").send_keys("개인 비번")
    time.sleep(2)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    logging.info("로그인 정보 입력 및 전송 완료")
    time.sleep(5)

#여기 부분은 구글 메일로 코드를 입력하라고 했을떄 사용하는 코드입니다 

    # # 새 창 열기 (구글 로그인 페이지 열기)
    # driver.execute_script("window.open('https://mail.google.com');")
    # time.sleep(2)

    # # 현재 창의 핸들 목록 확인 (새로운 창이 열리면 두 개의 핸들이 생깁니다)
    # window_handles = driver.window_handles

    # # 새로 열린 구글 로그인 창으로 전환 (두 번째 창)
    # driver.switch_to.window(window_handles[1])

    # # 구글 이메일 입력
    # google_email_input = driver.find_element(By.ID, "identifierId")
    # google_email_input.send_keys("")  # 구글 이메일 주소

    # # 이메일 '다음' 버튼 클릭
    # next_button = driver.find_element(By.ID, "identifierNext")
    # next_button.click()

    # time.sleep(5)

    # # 구글 비밀번호 입력
    # google_password_input = driver.find_element(By.NAME, "Passwd")
    # google_password_input.send_keys("")  # 구글 비밀번호

    # # 비밀번호 '다음' 버튼 클릭
    # google_next_button = driver.find_element(By.ID, "passwordNext")
    # google_next_button.click()

    # time.sleep(20)

    # # 페이지가 로드될 때까지 대기
    # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//table[@role="grid"]')))

    # try:
    #     # Instagram 보낸 이메일 중 첫 번째 항목 클릭
    #     instagram_mail = WebDriverWait(driver, 10).until(
    #         EC.element_to_be_clickable((
    #             By.XPATH,
    #             '(//span[@email="security@mail.instagram.com"]//ancestor::tr)[1]'
    #         ))
    #     )
    #     instagram_mail.click()
    # except Exception as e:
    #     print("Instagram 메일 클릭 실패:", e)
    #     raise

    # time.sleep(3)

    # try:
    #     # 'size'가 6인 <font> 태그 찾기 -> 입력 코드 유일 특징
    #     font_element = WebDriverWait(driver, 10).until(
    #         EC.presence_of_element_located((By.XPATH, "//font[@size='6']"))
    #     )
        
    #     # 해당 <font> 요소의 텍스트 값을 가져오기
    #     font_value = font_element.text
    #     another_variable = font_value
    #     print("가져온 값:", font_value)

    # except Exception as e:
    #     print("font 값 가져오기 실패:", e)
    #     raise

    # driver.close()

    # driver.switch_to.window(window_handles[0])
    # time.sleep(2)
    
    # # 이메일 입력창 찾고 변수 입력
    # email_input = driver.find_element(By.NAME, "email")
    # email_input.send_keys(font_value)

    # time.sleep(1)

    # # '계속' 버튼을 텍스트 기준으로 찾기 (XPath 사용)
    # continue_button = driver.find_element(By.XPATH, "//span[text()='계속']")
    # continue_button.click()

    # time.sleep(10)
    
    # driver.back()
#만약 구글 로그인해서 코드 가져올 필요가 없으면 이 코드는 필요 없습니다

    # '나중에 하기' 팝업 처리
    try:
        later_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[text()='나중에 하기']"))
        )
        later_button.click()
        logging.info("나중에 하기 버튼 클릭 완료")
    except (NoSuchElementException, TimeoutException):
        logging.info("나중에 하기 버튼 없음 - 스킵")

    time.sleep(3)

    # Reels 페이지 이동
    reels_link = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//a[@href="/reels/"]'))
    )
    reels_link.click()
    logging.info("Reels 페이지 이동 완료")
    time.sleep(3)


    # Reels 재생 위치 설정
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".x78zum5.xedcshv"))
    )
    actions = ActionChains(driver)
    actions.move_to_element(element).perform()

    # 5개 영상 시청 루프
    for i in range(5):
        logging.info(f"{i + 1}번째 영상 시청 중")
        time.sleep(16)
        actions.send_keys(Keys.PAGE_DOWN).perform()
        time.sleep(1)

    logging.info("모든 영상 시청 완료")


except WebDriverException as e:
    logging.error(f"웹드라이버 예외 발생: {e}")
except Exception as e:
    logging.error(f"알 수 없는 예외 발생: {e}")
finally:
    if driver:
        try:
            driver.quit()
            logging.info("WebDriver 정상 종료")
        except Exception as e:
            logging.warning(f"WebDriver 종료 중 예외 발생: {e}")
    
    # tshark 종료 처리
    if tshark_process.poll() is None:
        tshark_process.terminate()
        try:
            tshark_process.wait(timeout=5)
            logging.info("TShark 정상 종료")
        except subprocess.TimeoutExpired:
            tshark_process.kill()
            logging.warning("TShark 강제 종료됨")

    logging.info("프로그램 종료")

