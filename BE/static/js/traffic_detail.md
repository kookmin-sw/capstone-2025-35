# traffic_detail.js 명세서

## 개요
`traffic_detail.js`는 실시간 트래픽 모니터링 시스템의 상세 페이지에서 사용되는 JavaScript 파일입니다. 이 파일은 특정 IP 주소의 트래픽 데이터를 실시간으로 시각화하고 분석하는 기능을 제공합니다.

## 주요 기능

### 1. 소켓 연결 및 데이터 수신
- Socket.io를 사용하여 백엔드 서버와 실시간 통신
- 다양한 이벤트를 통해 트래픽 데이터, MAC 주소, 호스트명, 프로토콜 통계, 포트 통계, 패킷 로그, 스트리밍 서비스 감지 정보 등을 수신

### 2. 차트 시각화
- Chart.js 라이브러리를 사용하여 다양한 차트 구현
- 트래픽 차트: 다운로드/업로드 트래픽을 실시간으로 표시하는 라인 차트
- 프로토콜 차트: TCP, UDP, ICMP, 기타 프로토콜의 분포를 보여주는 도넛 차트
- 포트 차트: 가장 많이 사용되는 포트를 보여주는 바 차트
- 패턴 차트: 시간대별 트래픽 패턴을 보여주는 라인 차트

### 3. 데이터 포맷팅 및 계산
- 트래픽 크기 포맷팅 (B, KB, MB, GB)
- 시간 및 날짜 포맷팅
- 평균 속도 계산

### 4. 패킷 로그 관리
- 패킷 로그 데이터 저장 및 관리
- 페이지네이션 기능을 통한 로그 데이터 표시

### 5. UI 상호작용
- 차트 줌 인/아웃 및 리셋 기능
- 페이지네이션 컨트롤

## 이벤트 핸들러

### 페이지 로드 시 초기화
- 차트 초기화
- 이벤트 리스너 등록
- 모니터링 시작 시간 설정

### 소켓 이벤트 핸들러
1. `traffic_detail`: 실시간 트래픽 데이터 수신 및 차트 업데이트
2. `mac_update`: MAC 주소 정보 업데이트
3. `hostname_update`: 호스트명 정보 업데이트
4. `protocol_stats`: 프로토콜 통계 정보 업데이트
5. `port_stats`: 포트 사용량 통계 업데이트
6. `packet_log`: 패킷 로그 정보 업데이트
7. `streaming_detection`: 스트리밍 서비스 감지 정보 업데이트

## 함수 목록

### 차트 초기화 함수
- `initTrafficChart()`: 트래픽 차트 초기화
- `initProtocolChart()`: 프로토콜 차트 초기화
- `initPortChart()`: 포트 차트 초기화
- `initPatternChart()`: 패턴 차트 초기화

### 데이터 처리 함수
- `renderPacketLog()`: 패킷 로그 렌더링
- `formatTrafficSize(bytes)`: 트래픽 크기 포맷팅
- `formatTime(timestamp)`: 시간 포맷팅
- `formatDateTime(date)`: 날짜 및 시간 포맷팅
- `calculateAvgSpeed()`: 평균 속도 계산

## 백엔드 데이터 요구사항

### 1. traffic_detail 이벤트
```javascript
{
  ip: "192.168.1.1",  // IP 주소
  download: 12345,    // 다운로드 트래픽 (bytes)
  upload: 6789        // 업로드 트래픽 (bytes)
}
```

### 2. mac_update 이벤트
```javascript
{
  mac_dict: {
    "192.168.1.1": "00:1A:2B:3C:4D:5E",
    ...
  }
}
```

### 3. hostname_update 이벤트
```javascript
{
  ip: "192.168.1.1",
  hostname: "device-name.local"
}
```

### 4. protocol_stats 이벤트
```javascript
{
  ip: "192.168.1.1",
  tcp: 123,           // TCP 패킷 수
  udp: 456,           // UDP 패킷 수
  icmp: 7,            // ICMP 패킷 수
  other: 8            // 기타 프로토콜 패킷 수
}
```

### 5. port_stats 이벤트
```javascript
{
  ip: "192.168.1.1",
  ports: {
    "80": 123,        // 포트 번호: 패킷 수
    "443": 456,
    "8080": 78,
    ...
  }
}
```

### 6. packet_log 이벤트
```javascript
{
  ip: "192.168.1.1",
  packet: {
    time: 1616123456789,  // 타임스탬프 (밀리초)
    source: "192.168.1.5",  // 출발지 IP
    destination: "192.168.1.1",  // 목적지 IP
    protocol: "TCP",  // 프로토콜
    size: 1234,       // 패킷 크기 (bytes)
    info: "SYN, ACK"  // 추가 정보
  }
}
```

### 7. streaming_detection 이벤트
```javascript
{
  ip: "192.168.1.1",
  services: ["youtube", "netflix", ...]  // 감지된 스트리밍 서비스 목록
}
```

## 의존성
- Socket.io: 실시간 데이터 통신
- Chart.js: 차트 시각화
- chartjs-plugin-zoom: 차트 줌 기능
- chartjs-plugin-annotation: 차트 주석 기능

## 사용 방법
1. HTML 파일에 필요한 라이브러리와 함께 스크립트 포함:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.0/socket.io.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation"></script>
<script>
    // IP 주소 변수 설정 (템플릿에서 전달받은 값)
    const ip = "{{ data.ip }}";
</script>
<script src="{{ url_for('static', filename='js/traffic_detail.js') }}"></script>
```

2. HTML에 필요한 요소 포함:
   - 차트를 표시할 canvas 요소
   - 트래픽 정보를 표시할 요소
   - 패킷 로그를 표시할 테이블
   - 페이지네이션 컨트롤