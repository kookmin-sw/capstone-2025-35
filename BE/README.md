# 실시간 트래픽 모니터링 시스템 - UI 데모

이 프로젝트는 네트워크 트래픽을 실시간으로 모니터링하고 분석하는 시스템의 UI를 개선한 버전입니다. 스트리밍 서비스 감지 및 트래픽 패턴 분석 기능을 제공합니다.

## 데모 실행 방법

UI 데모를 확인하는 방법은 두 가지가 있습니다:

### 1. 정적 HTML 데모 (백엔드 연동 없음)

정적 HTML 파일을 통해 UI 디자인만 확인할 수 있습니다. 실제 데이터는 포함되어 있지 않습니다.

1. 브라우저에서 `BE/static/demo.html` 파일을 직접 열어서 확인합니다.

### 2. 동적 데모 (Python 백엔드 연동)

Python 백엔드를 실행하여 실시간으로 생성된 데이터와 함께 UI를 확인할 수 있습니다.

1. 필요한 패키지 설치:
   ```
   pip install -r requirements.txt
   ```

2. 데모 서버 실행:
   ```
   python BE/demo.py
   ```

3. 브라우저에서 다음 주소로 접속:
   ```
   http://localhost:5002
   ```

## 주요 기능

- **실시간 트래픽 모니터링**: 네트워크 트래픽을 실시간으로 모니터링하고 시각화
- **IP별 상세 정보**: 각 IP 주소별 상세 트래픽 정보 제공
- **프로토콜 분석**: TCP, UDP, ICMP 등 프로토콜별 트래픽 분포 시각화
- **포트 사용량 분석**: 주요 포트별 사용량 통계 제공
- **스트리밍 서비스 감지**: YouTube, Netflix 등 스트리밍 서비스 자동 감지
- **패킷 로그**: 상세 패킷 정보 로깅 및 조회 기능

## 파일 구조

- `BE/static/css/styles.css`: UI 스타일시트
- `BE/static/js/traffic_chart.js`: 차트 및 데이터 시각화 스크립트
- `BE/templates/index.html`: 메인 페이지 템플릿
- `BE/templates/traffic_detail.html`: 상세 페이지 템플릿
- `BE/templates/error.html`: 오류 페이지 템플릿
- `BE/demo.py`: 데모 데이터 생성 및 서버 실행 스크립트
- `BE/static/demo.html`: 정적 데모 HTML 파일

## 백엔드 연동 정보

실제 백엔드 구현 시 다음과 같은 Socket.IO 이벤트를 전송해야 합니다:

1. `traffic_total`: 전체 트래픽 데이터
2. `mac_update`: MAC 주소 정보
3. `streaming_detection`: 스트리밍 서비스 감지 정보
4. `traffic_detail`: 상세 트래픽 데이터
5. `protocol_stats`: 프로토콜 통계
6. `port_stats`: 포트 사용량 통계
7. `packet_log`: 패킷 로그 정보
8. `hostname_update`: 호스트명 정보

각 이벤트의 데이터 형식은 JavaScript 파일 내 주석을 참고하세요.