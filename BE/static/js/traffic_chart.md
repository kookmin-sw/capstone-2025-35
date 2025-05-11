# traffic_chart.js 함수 및 동작 방식 설명

이 문서는 `traffic_chart.js` 파일의 주요 함수들과 동작 방식을 설명합니다. 이 JavaScript 파일은 실시간 네트워크 트래픽 모니터링 시스템의 프론트엔드 부분을 담당하며, 백엔드에서 전송되는 트래픽 데이터를 시각화합니다.

## 1. 개요

`traffic_chart.js`는 Socket.io를 사용하여 백엔드 서버와 실시간 통신하며, Chart.js를 활용하여 네트워크 트래픽 데이터를 시각적으로 표현합니다. 주요 기능으로는:

- 실시간 트래픽 데이터 시각화
- IP별 트래픽 모니터링
- MAC 주소 표시
- 스트리밍 서비스 감지
- 모니터링 시간 및 총 트래픽량 표시

## 2. 전역 변수

```javascript
const socket = io.connect("http://localhost:5002");
const charts = {};  // IP별 차트 저장
let macDict = {}; // MAC 주소 저장용 객체
let maxSize = 80000;
let period = 20;
let monitoringStartTime = new Date();
let totalTrafficBytes = 0;
let detectedStreamingApps = new Set();
```

- `socket`: Socket.io 연결 객체로, 백엔드 서버와의 실시간 통신을 담당
- `charts`: IP 주소를 키로 하여 해당 IP의 차트 객체를 저장하는 객체
- `macDict`: IP 주소를 키로 하여 해당 IP의 MAC 주소를 저장하는 객체
- `maxSize`: 차트에 표시할 최대 데이터 크기
- `period`: 차트에 표시할 시간 범위(초)
- `monitoringStartTime`: 모니터링 시작 시간
- `totalTrafficBytes`: 총 트래픽 바이트 수
- `detectedStreamingApps`: 감지된 스트리밍 서비스 목록을 저장하는 Set 객체

## 3. 초기화 및 기본 설정

### 페이지 로드 시 초기화
```javascript
document.addEventListener('DOMContentLoaded', function() {
    // 모니터링 시간 업데이트 시작
    updateMonitoringTime();
    setInterval(updateMonitoringTime, 1000);
    
    // 테이블 컨테이너 초기화
    createTable();
});
```

페이지 로드 시 실행되는 함수로, 모니터링 시간을 1초마다 업데이트하고 트래픽 정보를 표시할 테이블을 생성합니다.

### Chart.js 기본 설정
```javascript
Chart.defaults.font.family = "'Noto Sans KR', 'Roboto', sans-serif";
Chart.defaults.color = '#2c3e50';
Chart.register(ChartZoom);
```

Chart.js의 기본 폰트와 색상을 설정하고, 차트 확대/축소 기능을 위한 플러그인을 등록합니다.

## 4. 유틸리티 함수

### 모니터링 시간 업데이트
```javascript
function updateMonitoringTime() {
    const now = new Date();
    const diffInSeconds = Math.floor((now - monitoringStartTime) / 1000);
    
    let timeDisplay;
    if (diffInSeconds < 60) {
        timeDisplay = `${diffInSeconds}초`;
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        const seconds = diffInSeconds % 60;
        timeDisplay = `${minutes}분 ${seconds}초`;
    } else {
        const hours = Math.floor(diffInSeconds / 3600);
        const minutes = Math.floor((diffInSeconds % 3600) / 60);
        timeDisplay = `${hours}시간 ${minutes}분`;
    }
    
    document.getElementById('monitoring-time').textContent = timeDisplay;
}
```

모니터링 시작 시간부터 현재까지의 경과 시간을 계산하여 화면에 표시합니다. 시간 형식은 경과 시간에 따라 초, 분, 시간 단위로 자동 변환됩니다.

### 트래픽 크기 포맷팅
```javascript
function formatTrafficSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB';
    else if (bytes < 1073741824) return (bytes / 1048576).toFixed(2) + ' MB';
    else return (bytes / 1073741824).toFixed(2) + ' GB';
}
```

바이트 단위의 트래픽 크기를 사람이 읽기 쉬운 형태(B, KB, MB, GB)로 변환합니다.

### 트래픽 상태에 따른 색상 반환
```javascript
function getTrafficStatusColor(bytesPerSecond) {
    if (bytesPerSecond > 500000) return '#e74c3c'; // 높음 (빨강)
    if (bytesPerSecond > 100000) return '#f39c12'; // 중간 (주황)
    return '#2ecc71'; // 낮음 (초록)
}
```

초당 트래픽 바이트 수에 따라 적절한 색상을 반환합니다:
- 500,000 바이트/초 초과: 빨간색 (높음)
- 100,000 바이트/초 초과: 주황색 (중간)
- 그 외: 초록색 (낮음)

## 5. UI 관련 함수

### 표 동적 생성
```javascript
function createTable() {
    let tableContainer = document.getElementById("table-container");
    tableContainer.innerHTML = `
        <table class="traffic-info-table">
            <thead>
                <tr>
                    <th><i class="fas fa-network-wired"></i> IP 주소</th>
                    <th><i class="fas fa-ethernet"></i> MAC 주소</th>
                    <th><i class="fas fa-chart-line"></i> 트래픽 그래프</th>
                    <th><i class="fas fa-stream"></i> 스트리밍 서비스</th>
                    <th><i class="fas fa-search-plus"></i> 상세보기</th>
                </tr>
            </thead>
            <tbody id="table-body"></tbody>
        </table>
    `;
}
```

트래픽 정보를 표시할 테이블의 기본 구조를 생성합니다. 테이블은 IP 주소, MAC 주소, 트래픽 그래프, 스트리밍 서비스, 상세보기 버튼 열로 구성됩니다.

### 새로운 IP 행 추가
```javascript
function addRow(ip) {
    let tableBody = document.getElementById("table-body");

    let row = document.createElement("tr");
    row.innerHTML = `
        <td>
            <a href="/traffic/${ip}" class="ip-link">${ip}</a>
        </td>
        <td id="mac-${ip}">
            <div class="loading"></div> 로딩 중...
        </td>
        <td id="chart-container-${ip}">
            <canvas id="mini-chart-${ip}" width="200" height="60"></canvas>
        </td>
        <td id="streaming-${ip}">
            <span class="app-badge">감지 중...</span>
        </td>
        <td>
            <button onclick="goToDetail('${ip}')" class="detail-btn">
                <i class="fas fa-chart-bar"></i> 상세 보기
            </button>
        </td>
    `;
    tableBody.appendChild(row);
    
    // 미니 차트 생성
    createMiniChart(ip);
    
    // 모니터링 중인 IP 카운트 업데이트
    updateMonitoredIpCount();
}
```

새로운 IP 주소에 대한 행을 테이블에 추가합니다. 각 행은 IP 주소, MAC 주소, 미니 차트, 스트리밍 서비스 정보, 상세 보기 버튼을 포함합니다. 행 추가 후 해당 IP의 미니 차트를 생성하고 모니터링 중인 IP 개수를 업데이트합니다.

### 상세 페이지 이동 함수
```javascript
function goToDetail(ip) {
    window.location.href = `/traffic/${ip}`;
}
```

특정 IP의 상세 정보 페이지로 이동하는 함수입니다.

### 모니터링 중인 IP 카운트 업데이트
```javascript
function updateMonitoredIpCount() {
    const count = Object.keys(charts).length;
    document.getElementById('monitored-ip-count').textContent = count;
}
```

현재 모니터링 중인 IP 주소의 개수를 계산하여 화면에 표시합니다.

### 총 트래픽량 업데이트
```javascript
function updateTotalTraffic(newBytes) {
    totalTrafficBytes += newBytes;
    document.getElementById('total-traffic').textContent = formatTrafficSize(totalTrafficBytes);
}
```

새로운 트래픽 데이터가 수신될 때마다 총 트래픽량을 업데이트하고 화면에 표시합니다.

### 스트리밍 서비스 감지 업데이트
```javascript
function updateDetectedStreaming(services) {
    if (services && services.length > 0) {
        services.forEach(service => detectedStreamingApps.add(service));
    }
    document.getElementById('detected-streaming').textContent = detectedStreamingApps.size;
}
```

감지된 스트리밍 서비스 목록을 업데이트하고 총 감지된 서비스 개수를 화면에 표시합니다.

## 6. 차트 관련 함수

### 미니 차트 생성
```javascript
function createMiniChart(ip) {
    const ctx = document.getElementById(`mini-chart-${ip}`).getContext('2d');
    
    const miniChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '트래픽',
                data: [],
                borderColor: '#3498db',
                borderWidth: 2,
                pointRadius: 0,
                fill: true,
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            // 차트 옵션 설정...
        }
    });
    
    return miniChart;
}
```

테이블 내에 표시될 작은 크기의 라인 차트를 생성합니다. 이 차트는 해당 IP의 트래픽 추이를 간략하게 보여줍니다.

### 메인 차트 생성
```javascript
function createChart(ip) {
    // 테이블에 행이 없으면 생성
    if (!document.getElementById("table-body")) {
        createTable();
    }
    
    // 행이 없으면 추가
    if (!document.getElementById(`chart-container-${ip}`)) {
        addRow(ip);
    }
    
    // 차트 컨테이너 생성
    let chartSection = document.createElement("div");
    chartSection.className = "chart-wrapper";
    chartSection.innerHTML = `
        <div class="ip-label"><i class="fas fa-network-wired"></i> ${ip}</div>
        <div class="chart-container">
            <canvas id="chart-${ip}"></canvas>
        </div>
    `;
    
    document.getElementById("charts").appendChild(chartSection);
    
    // 차트 생성
    let ctx = document.getElementById(`chart-${ip}`).getContext("2d");
    
    charts[ip] = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: "트래픽 (bytes)",
                data: [],
                borderColor: '#3498db',
                borderWidth: 2,
                pointRadius: 1,
                pointHoverRadius: 5,
                fill: true,
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            // 차트 옵션 설정...
        }
    });
}
```

특정 IP 주소에 대한 메인 차트를 생성합니다. 이 차트는 페이지 하단에 표시되며, 해당 IP의 트래픽 데이터를 더 자세하게 보여줍니다. 차트는 확대/축소 및 패닝 기능을 지원합니다.

## 7. Socket.io 이벤트 처리

### 트래픽 데이터 수신
```javascript
socket.on("traffic_total", function (data) {
    let secondsPassed = data.seconds_passed;
    let trafficData = data.traffic_total;
    let newTrafficBytes = 0;

    Object.keys(trafficData).forEach((ip) => {
        // 차트가 없으면 생성
        if (!charts[ip]) {
            createChart(ip);
        }

        // 미니 차트 업데이트
        let miniChart = Chart.getChart(`mini-chart-${ip}`);
        if (miniChart) {
            // 미니 차트 데이터 업데이트 로직...
        }

        // 메인 차트 업데이트
        let chart = charts[ip];
        if (chart) {
            // 메인 차트 데이터 업데이트 로직...
        }
    });
    
    // 총 트래픽량 업데이트
    updateTotalTraffic(newTrafficBytes);
    
    // 스트리밍 서비스 감지
    if (data.detected_services) {
        updateDetectedStreaming(data.detected_services);
    }
});
```

백엔드에서 전송하는 트래픽 데이터를 수신하여 처리하는 이벤트 핸들러입니다. 수신된 데이터를 기반으로:
1. 새로운 IP가 감지되면 해당 IP에 대한 차트 생성
2. 기존 IP의 미니 차트와 메인 차트 업데이트
3. 총 트래픽량 업데이트
4. 감지된 스트리밍 서비스 업데이트

### MAC 주소 업데이트 이벤트
```javascript
socket.on("mac_update", function(data) {
    macDict = data.mac_dict;
    
    // 각 IP에 대한 MAC 주소 업데이트
    Object.keys(macDict).forEach(ip => {
        const macElement = document.getElementById(`mac-${ip}`);
        if (macElement) {
            macElement.innerHTML = macDict[ip];
        }
    });
});
```

백엔드에서 전송하는 MAC 주소 정보를 수신하여 각 IP에 대한 MAC 주소를 화면에 표시합니다.

### 스트리밍 서비스 감지 이벤트
```javascript
socket.on("streaming_detection", function(data) {
    const ip = data.ip;
    const services = data.services;
    
    if (services && services.length > 0) {
        const streamingElement = document.getElementById(`streaming-${ip}`);
        if (streamingElement) {
            streamingElement.innerHTML = services.map(service => {
                return `<span class="app-badge app-${service.toLowerCase()}">${service}</span>`;
            }).join(' ');
        }
        
        updateDetectedStreaming(services);
    }
});
```

백엔드에서 특정 IP에서 감지된 스트리밍 서비스 정보를 수신하여 화면에 표시합니다.

## 8. 기타 이벤트 처리

```javascript
document.getElementById('about-link').addEventListener('click', function(e) {
    e.preventDefault();
    alert('실시간 트래픽 모니터링 시스템\n\n네트워크 트래픽을 실시간으로 모니터링하고 분석하는 시스템입니다.\n스트리밍 서비스 감지 및 트래픽 패턴 분석 기능을 제공합니다.');
});
```

About 링크 클릭 시 시스템에 대한 간략한 설명을 알림창으로 표시합니다.

## 9. HTML과의 상호작용

`traffic_chart.js`는 `index.html`의 다음 요소들과 상호작용합니다:

1. **대시보드 요약 정보**
   - `#monitored-ip-count`: 모니터링 중인 IP 개수 표시
   - `#total-traffic`: 총 트래픽량 표시
   - `#monitoring-time`: 모니터링 경과 시간 표시
   - `#detected-streaming`: 감지된 스트리밍 서비스 개수 표시

2. **테이블 컨테이너**
   - `#table-container`: 트래픽 정보 테이블이 동적으로 생성되는 컨테이너

3. **차트 컨테이너**
   - `#charts`: IP별 메인 차트가 동적으로 생성되는 컨테이너

4. **기타**
   - `#about-link`: About 링크 클릭 이벤트 처리

## 10. 데이터 흐름

1. 백엔드 서버는 Socket.io를 통해 실시간으로 트래픽 데이터, MAC 주소 정보, 스트리밍 서비스 감지 정보를 전송합니다.
2. 프론트엔드는 이 데이터를 수신하여 차트와 테이블을 업데이트합니다.
3. 사용자는 특정 IP의 상세 정보를 보기 위해 상세 보기 버튼을 클릭할 수 있습니다.
4. 차트는 실시간으로 업데이트되며, 트래픽 상태에 따라 색상이 변경됩니다.

## 11. 결론

`traffic_chart.js`는 Socket.io와 Chart.js를 활용하여 실시간 네트워크 트래픽 모니터링 시스템의 프론트엔드를 구현합니다. 이 파일은 백엔드에서 전송되는 데이터를 시각적으로 표현하고, 사용자가 네트워크 트래픽 상태를 쉽게 파악할 수 있도록 도와줍니다.