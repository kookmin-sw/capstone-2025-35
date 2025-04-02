// 전역 변수 설정
const socket = io.connect("http://localhost:5002");
const charts = {};  // IP별 차트 저장
let macDict = {}; // MAC 주소 저장용 객체
let maxSize = 80000;
let period = 20;
let monitoringStartTime = new Date();
let totalTrafficBytes = 0;
let detectedStreamingApps = new Set();

// Chart.js 기본 설정
Chart.defaults.font.family = "'Noto Sans KR', 'Roboto', sans-serif";
Chart.defaults.color = '#2c3e50';

// Chart.js Zoom 플러그인 등록
Chart.register(ChartZoom);

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 모니터링 시간 업데이트 시작
    updateMonitoringTime();
    setInterval(updateMonitoringTime, 1000);
    
    // 테이블 컨테이너 초기화
    createTable();
});

// 모니터링 시간 업데이트
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

// 트래픽 크기 포맷팅 (바이트 -> KB, MB, GB)
function formatTrafficSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB';
    else if (bytes < 1073741824) return (bytes / 1048576).toFixed(2) + ' MB';
    else return (bytes / 1073741824).toFixed(2) + ' GB';
}

// 표 동적 생성
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

// 새로운 IP 행 추가
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

// 미니 차트 생성
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
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: true,
                    callbacks: {
                        label: function(context) {
                            return formatTrafficSize(context.raw);
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    display: false,
                    beginAtZero: true
                }
            },
            animation: false
        }
    });
    
    return miniChart;
}

// 상세 페이지 이동 함수
function goToDetail(ip) {
    window.location.href = `/traffic/${ip}`;
}

// 모니터링 중인 IP 카운트 업데이트
function updateMonitoredIpCount() {
    const count = Object.keys(charts).length;
    document.getElementById('monitored-ip-count').textContent = count;
}

// 총 트래픽량 업데이트
function updateTotalTraffic(newBytes) {
    totalTrafficBytes += newBytes;
    document.getElementById('total-traffic').textContent = formatTrafficSize(totalTrafficBytes);
}

// 스트리밍 서비스 감지 업데이트
function updateDetectedStreaming(services) {
    if (services && services.length > 0) {
        services.forEach(service => detectedStreamingApps.add(service));
    }
    document.getElementById('detected-streaming').textContent = detectedStreamingApps.size;
}

// 트래픽 상태에 따른 색상 반환
function getTrafficStatusColor(bytesPerSecond) {
    if (bytesPerSecond > 500000) return '#e74c3c'; // 높음 (빨강)
    if (bytesPerSecond > 100000) return '#f39c12'; // 중간 (주황)
    return '#2ecc71'; // 낮음 (초록)
}

/**
 * 소켓 이벤트 처리: 트래픽 데이터 수신
 * 
 * 백엔드에서 전송해야 하는 데이터 형식:
 * {
 *   seconds_passed: Number,  // 모니터링 시작 이후 경과 시간(초)
 *   traffic_total: {         // IP별 트래픽 데이터
 *     "192.168.1.1": [123, 456, 789, ...],  // 각 초마다의 트래픽 바이트 수
 *     "192.168.1.2": [234, 567, 890, ...],
 *     ...
 *   },
 *   detected_services: ["youtube", "netflix", ...]  // 감지된 스트리밍 서비스 목록 (선택적)
 * }
 */
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
            let val = Math.min(Math.max(0, trafficData[ip].length - period - 1) + miniChart.data.labels.length, period - 1);
            let label = Math.max(0, secondsPassed - period - 1) + miniChart.data.labels.length;
            
            // 새 데이터 추가
            while (label < secondsPassed) {
                const trafficValue = trafficData[ip][val++] || 0;
                miniChart.data.labels.push(label++);
                miniChart.data.datasets[0].data.push(trafficValue);
                newTrafficBytes += trafficValue;
            }
            
            // 오래된 데이터 제거
            while (miniChart.data.labels.length > period) {
                miniChart.data.labels.shift();
                miniChart.data.datasets[0].data.shift();
            }
            
            // 트래픽 상태에 따른 색상 변경
            const latestTraffic = miniChart.data.datasets[0].data[miniChart.data.datasets[0].data.length - 1] || 0;
            miniChart.data.datasets[0].borderColor = getTrafficStatusColor(latestTraffic);
            miniChart.data.datasets[0].backgroundColor = `${getTrafficStatusColor(latestTraffic)}20`; // 20% 투명도
            
            miniChart.update('none');
        }

        // 메인 차트 업데이트
        let chart = charts[ip];
        if (chart) {
            let val = Math.min(Math.max(0, trafficData[ip].length - period - 1) + chart.data.labels.length, period - 1);
            let label = Math.max(0, secondsPassed - period - 1) + chart.data.labels.length;
            
            while (label < secondsPassed) {
                chart.data.labels.push(label++);
                chart.data.datasets[0].data.push(trafficData[ip][val++] || 0);
            }
            
            while (chart.data.labels.length > period) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }
            
            chart.update('none');
        }
    });
    
    // 총 트래픽량 업데이트
    updateTotalTraffic(newTrafficBytes);
    
    // 스트리밍 서비스 감지
    if (data.detected_services) {
        updateDetectedStreaming(data.detected_services);
    }
});

/**
 * MAC 주소 업데이트 이벤트
 * 
 * 백엔드에서 전송해야 하는 데이터 형식:
 * {
 *   mac_dict: {
 *     "192.168.1.1": "00:1A:2B:3C:4D:5E",
 *     "192.168.1.2": "AA:BB:CC:DD:EE:FF",
 *     ...
 *   }
 * }
 */
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

/**
 * 스트리밍 서비스 감지 이벤트
 * 
 * 백엔드에서 전송해야 하는 데이터 형식:
 * {
 *   ip: "192.168.1.1",  // 감지된 IP 주소
 *   services: ["youtube", "netflix", ...]  // 해당 IP에서 감지된 스트리밍 서비스 목록
 * }
 */
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

/**
 * 호스트명 업데이트 이벤트 (traffic_detail.html 페이지에서 사용)
 * 
 * 백엔드에서 전송해야 하는 데이터 형식:
 * {
 *   ip: "192.168.1.1",  // IP 주소
 *   hostname: "device-name.local"  // 호스트명
 * }
 */
socket.on("hostname_update", function(data) {
    const hostnameElement = document.getElementById('hostname');
    if (hostnameElement && data.hostname) {
        hostnameElement.textContent = data.hostname;
    }
});

/**
 * 상세 트래픽 데이터 이벤트 (traffic_detail.html 페이지에서 사용)
 * 
 * 백엔드에서 전송해야 하는 데이터 형식:
 * {
 *   ip: "192.168.1.1",  // IP 주소
 *   download: 12345,    // 다운로드 트래픽 (bytes)
 *   upload: 6789        // 업로드 트래픽 (bytes)
 * }
 */
socket.on("traffic_detail", function(data) {
    // traffic_detail.html 페이지에서 처리
});

/**
 * 프로토콜 통계 이벤트 (traffic_detail.html 페이지에서 사용)
 * 
 * 백엔드에서 전송해야 하는 데이터 형식:
 * {
 *   ip: "192.168.1.1",  // IP 주소
 *   tcp: 123,           // TCP 패킷 수
 *   udp: 456,           // UDP 패킷 수
 *   icmp: 7,            // ICMP 패킷 수
 *   other: 8            // 기타 프로토콜 패킷 수
 * }
 */
socket.on("protocol_stats", function(data) {
    // traffic_detail.html 페이지에서 처리
});

/**
 * 포트 통계 이벤트 (traffic_detail.html 페이지에서 사용)
 * 
 * 백엔드에서 전송해야 하는 데이터 형식:
 * {
 *   ip: "192.168.1.1",  // IP 주소
 *   ports: {
 *     "80": 123,        // 포트 번호: 패킷 수
 *     "443": 456,
 *     "8080": 78,
 *     ...
 *   }
 * }
 */
socket.on("port_stats", function(data) {
    // traffic_detail.html 페이지에서 처리
});

/**
 * 패킷 로그 이벤트 (traffic_detail.html 페이지에서 사용)
 * 
 * 백엔드에서 전송해야 하는 데이터 형식:
 * {
 *   ip: "192.168.1.1",  // IP 주소
 *   packet: {
 *     time: 1616123456789,  // 타임스탬프 (밀리초)
 *     source: "192.168.1.5",  // 출발지 IP
 *     destination: "192.168.1.1",  // 목적지 IP
 *     protocol: "TCP",  // 프로토콜
 *     size: 1234,       // 패킷 크기 (bytes)
 *     info: "SYN, ACK"  // 추가 정보
 *   }
 * }
 */
socket.on("packet_log", function(data) {
    // traffic_detail.html 페이지에서 처리
});

// 메인 차트 생성
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
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 12,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return formatTrafficSize(context.raw);
                        }
                    }
                },
                zoom: {
                    pan: {
                        enabled: true,
                        mode: 'x'
                    },
                    zoom: {
                        wheel: {
                            enabled: true
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'x'
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: "경과 시간 (초)"
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: "트래픽량 (bytes)"
                    },
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatTrafficSize(value);
                        }
                    }
                }
            },
            animation: {
                duration: 300
            }
        }
    });
}

// 어바웃 링크 클릭 이벤트
document.getElementById('about-link').addEventListener('click', function(e) {
    e.preventDefault();
    alert('실시간 트래픽 모니터링 시스템\n\n네트워크 트래픽을 실시간으로 모니터링하고 분석하는 시스템입니다.\n스트리밍 서비스 감지 및 트래픽 패턴 분석 기능을 제공합니다.');
});