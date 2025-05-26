# FLOWTRACER | 암호화 트래픽 패킷 길이를 이용한 어플리케이션 식별
---
2025 국민대학교 소프트웨어학부 캡스톤 디자인 35조 | 국민대학교 정보보호연구실 & (주)시스메이트

## 1. 프로젝트 소개

![최종본](https://github.com/user-attachments/assets/e9948d1d-fc53-4e87-996d-9bd5c242d222)

현대 네트워크 환경에서는 점점 더 많은 트래픽들이 암호화되면서, 기존의 패킷 기반 분석 기술만으로는 어플리케이션을 정확히 식별하기 어려워지고 있습니다. 이는 보안 위협 대응과 네트워크 리소스 관리에 제약을 주며, 결과적으로 관리 비용 상승이라는 현실적인 문제로 이어지고 있습니다.

FLOWTRACER는 이러한 문제를 해결하기 위해 개발된 패킷 플로우 기반 어플리케이션 식별 시스템입니다. 암호화된 패킷 컨텐츠를 분석하는 대신, 패킷 플로우 패턴을 활용해 암호화 수준이 높은 트래픽에서도 어플리케이션을 정확하게 식별할 수 있도록 설계 되었습니다.

이 기술을 통해 암호화된 트래픽에서도 어플리케이션 식별이 가능해지며 다음과 같은 보안 및 네트워크 운영 측면의 비용 절감 효과를 기대할 수 있습니다.

- 네트워크 관리자 측면 : 비인가 어플리케이션 차단, 트래픽 우선순위 설정 등을 통해 트래픽 관리에 비용 절감
- 보안 관리자 측면 : 어플리케이션 기반 이상현상 탐지 비용 감소

## 2. 주요 기능

1. 트래픽 정보 시각화
    
    ![Image](https://github.com/user-attachments/assets/42d97cbe-694d-48f1-af03-f9f0f53d3885)
    
    클라이언트 별 네트워크 리소스 사용량 시각화
    
2. 어플리케이션 식별
    
    ![Image](https://github.com/user-attachments/assets/6a3d2708-78a7-40c0-93c9-9634d9ef977f)
    
    개별 패킷의 패턴 분석 및 어플리케이션 식별 결과 제공
    
3. 식별 어플리케이션 차단 기능
    
    ![Image](https://github.com/user-attachments/assets/4e0be355-d5be-4a82-8b9d-f4a2d673dbb1)
    
    특정 어플리케이션 트래픽 선택적 차단 가능
    

## 3. 팀 소개

| 담당 | 이름 |
| --- | --- |
| 팀장 | 민수홍 |
| 팀원 | 전홍선 |
| 팀원 | 장승훈 |
| 팀원 | 박도현 |
| 팀원 | 서동현 |
| 지도교수 | 윤명근 |

## 4. 사용환경 설정 및 시작하기(macos, apple silicon기준)

### 의존성 설치

(bash)
```bash
pip3 install -r requirements.txt
```

### MySQL설치 및 DB생성

(bash)
```bash
brew install mysql
brew services start mysql
mysql -u root -p
```
초기 비밀번호는 존재하지 않으므로 Enter입력

(sql)
```sql
CREATE DATABASE packet_logs_db;
SHOW DATABASES;
```
packet_logs_db가 출력된다면 성공

sql프롬프트 나가는 법(sql)
```sql
exit;
```

### [차단기능](https://github.com/kookmin-sw/capstone-2025-35/blob/master/BE/README.md)

### 웹사이트 실행

(bash)
```bash
python3 app.py
```

### 실행 후 데이터베이스 확인 방법
- 클라이언트 세부 페이지 들어가야 패킷이 수집됩니다.

(bash)
```bash
mysql -u root -p
```

(sql)
```sql
USE packet_logs_db;
SELECT * FROM packet_log;
```

## 5. 폴더 구조

```bash
capstone-2025-35/
├── BE/                          # Flask기반 백엔드 어플리케이션 디렉토리
│   ├── DB/                      # 데이터베이스 관련 모듈
│   ├── static/                  # 정적 데이터(css, img)관련 파일
│   ├── templates/               # HTML 템플릿 파일
│   ├── app.py                   # Flask 백엔드 서버 실행 메인 파일
│   └── ...
├── DataCollection/              # 데이터 전처리 관련 파일
│   ├── auto_flow/               # 데이터 자동수집 파일
│   └── to_df.py                 # 수집한 데이터 DataFrame으로 변환
├── Documents/                   # 프로젝트 문서 및 보고서 자료
├── experiment/                  # 실험용 코드 저장소
│   └── tf_idf_classification.py # tf-idf기반 분류 성능 실험 코드
├── pkl/                         # 모델 학습 결과 파일 저장
├── suricata/                    # 차단 기능 구현
├── README.md                    # 프로젝트 README 파일
├── create_config.py             # IP설정 및 초기 환경 구성
├── requirements.txt             # Python 패키지 의존성 목록
└── ...
```

## 5. 소개 자료

- [중간발표ppt](https://github.com/kookmin-sw/capstone-2025-35/blob/master/Documents/%EC%A4%91%EA%B0%84%20%EB%B0%9C%ED%91%9C.pptx)

- 최종 발표 ppt(추후 추가)

- [포스터](https://github.com/kookmin-sw/capstone-2025-35/blob/master/Documents/%ED%8F%AC%EC%8A%A4%ED%84%B0.png)
