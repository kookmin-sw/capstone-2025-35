/**
 * 트래픽 상세 페이지 스크립트
 * 
 * 백엔드에서 전송해야 하는 데이터:
 * 1. traffic_detail 이벤트: 특정 IP의 실시간 트래픽 데이터
 *    {
 *      ip: "192.168.1.1",  // IP 주소
 *      download: 12345,    // 다운로드 트래픽 (bytes)
 *      upload: 6789        // 업로드 트래픽 (bytes)
 *    }
 * 
 * 2. mac_update 이벤트: IP별 MAC 주소 정보
 *    {
 *      mac_dict: {
 *        "192.168.1.1": "00:1A:2B:3C:4D:5E",
 *        ...
 *      }
 *    }
 * 
 * 3. hostname_update 이벤트: IP의 호스트명 정보
 *    {
 *      ip: "192.168.1.1",
 *      hostname: "device-name.local"
 *    }
 * 
 * 4. protocol_stats 이벤트: 프로토콜 통계 정보
 *    {
 *      ip: "192.168.1.1",
 *      tcp: 123,           // TCP 패킷 수
 *      udp: 456,           // UDP 패킷 수
 *      icmp: 7,            // ICMP 패킷 수
 *      other: 8            // 기타 프로토콜 패킷 수
 *    }
 * 
 * 5. port_stats 이벤트: 포트 사용량 통계
 *    {
 *      ip: "192.168.1.1",
 *      ports: {
 *        "80": 123,        // 포트 번호: 패킷 수
 *        "443": 456,
 *        "8080": 78,
 *        ...
 *      }
 *    }
 * 
 * 6. packet_log 이벤트: 패킷 로그 정보
 *    {
 *      ip: "192.168.1.1",
 *      packet: {
 *        time: 1616123456789,  // 타임스탬프 (밀리초)
 *        source: "192.168.1.5",  // 출발지 IP
 *        destination: "192.168.1.1",  // 목적지 IP
 *        protocol: "TCP",  // 프로토콜
 *        size: 1234,       // 패킷 크기 (bytes)
 *        info: "SYN, ACK"  // 추가 정보
 *      }
 *    }
 * 
 * 7. streaming_detection 이벤트: 스트리밍 서비스 감지 정보
 *    {
 *      ip: "192.168.1.1",
 *      services: ["youtube", "netflix", ...]  // 감지된 스트리밍 서비스 목록
 *    }
 */
// 소켓 연결
const socket = io.connect("http://localhost:5002");
// IP 주소는 HTML 템플릿에서 전달받음 (161번 줄 참조)
let trafficChart, protocolChart, portChart, patternChart;
let packetLog = [];
let currentPage = 1;
let itemsPerPage = 10;
let totalTrafficDown = 0;
let totalTrafficUp = 0;
let maxSpeed = 0;
let speedHistory = [];
let monitoringStartTime = new Date();

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 트래픽 상세 페이지 접속 이벤트 발생
    socket.emit('join_traffic_detail', { ip: ip });
    // 차트 초기화
    initTrafficChart();
    initProtocolChart();
    initPortChart();
    initPatternChart();
    
    // 줌 컨트롤 이벤트 리스너
    document.getElementById('zoom-in').addEventListener('click', function() {
        trafficChart.zoom(1.1);
    });
    
    document.getElementById('zoom-out').addEventListener('click', function() {
        trafficChart.zoom(0.9);
    });
    
    document.getElementById('reset-zoom').addEventListener('click', function() {
        trafficChart.resetZoom();
    });
    
    // 페이지네이션 이벤트 리스너
    document.getElementById('prev-page').addEventListener('click', function() {
        if (currentPage > 1) {
            currentPage--;
            renderPacketLog();
        }
    });
    
    document.getElementById('next-page').addEventListener('click', function() {
        const maxPage = Math.ceil(packetLog.length / itemsPerPage);
        if (currentPage < maxPage) {
            currentPage++;
            renderPacketLog();
        }
    });
    
    // 모니터링 시작 시간 설정
    document.getElementById('monitoring-start').textContent = formatDateTime(monitoringStartTime);
});

// 트래픽 차트 초기화
function initTrafficChart() {
    const ctx = document.getElementById('traffic-chart').getContext('2d');
    trafficChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: '다운로드',
                    data: [],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: '업로드',
                    data: [],
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }
            ]
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
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatTrafficSize(context.raw) + '/s';
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
                    title: {
                        display: true,
                        text: '시간'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '트래픽 (bytes/s)'
                    },
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatTrafficSize(value);
                        }
                    }
                }
            }
        }
    });
}

// 프로토콜 차트 초기화
function initProtocolChart() {
    const ctx = document.getElementById('protocol-chart').getContext('2d');
    protocolChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['TCP', 'UDP', 'ICMP', 'Other'],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: [
                    '#3498db',
                    '#2ecc71',
                    '#f39c12',
                    '#95a5a6'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// 포트 차트 초기화
function initPortChart() {
    const ctx = document.getElementById('port-chart').getContext('2d');
    portChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: '패킷 수',
                data: [],
                backgroundColor: '#3498db',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 패턴 차트 초기화
function initPatternChart() {
    const ctx = document.getElementById('pattern-chart').getContext('2d');
    patternChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'],
            datasets: [{
                label: '트래픽 패턴',
                data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                borderColor: '#9b59b6',
                backgroundColor: 'rgba(155, 89, 182, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatTrafficSize(value);
                        }
                    }
                }
            }
        }
    });
}

// 패킷 로그 렌더링
function renderPacketLog() {
    const tbody = document.getElementById('packet-log');
    const start = (currentPage - 1) * itemsPerPage;
    const end = Math.min(start + itemsPerPage, packetLog.length);
    
    if (packetLog.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="no-data">패킷 데이터가 없습니다.</td></tr>';
        return;
    }
    
    let html = '';
    for (let i = start; i < end; i++) {
        const packet = packetLog[i];
        html += `
            <tr>
                <td>${formatTime(packet.time)}</td>
                <td>${packet.source}</td>
                <td>${packet.destination}</td>
                <td>${packet.protocol}</td>
                <td>${formatTrafficSize(packet.size)}</td>
                <td>${packet.info}</td>
            </tr>
        `;
    }
    
    tbody.innerHTML = html;
    
    // 페이지네이션 업데이트
    const maxPage = Math.ceil(packetLog.length / itemsPerPage);
    document.getElementById('page-info').textContent = `페이지 ${currentPage} / ${maxPage}`;
    document.getElementById('prev-page').disabled = currentPage === 1;
    document.getElementById('next-page').disabled = currentPage === maxPage;
}

// 트래픽 크기 포맷팅
function formatTrafficSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB';
    else if (bytes < 1073741824) return (bytes / 1048576).toFixed(2) + ' MB';
    else return (bytes / 1073741824).toFixed(2) + ' GB';
}

// 시간 포맷팅
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// 날짜 및 시간 포맷팅
function formatDateTime(date) {
    return date.toLocaleString('ko-KR', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit',
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
    });
}

// 평균 속도 계산
function calculateAvgSpeed() {
    if (speedHistory.length === 0) return 0;
    const sum = speedHistory.reduce((a, b) => a + b, 0);
    return sum / speedHistory.length;
}

// 소켓 이벤트: 상세 트래픽 데이터
socket.on('traffic_detail', function(data) {
    if (data.ip !== ip) return;
    
    const timestamp = new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    
    // 트래픽 차트 업데이트
    trafficChart.data.labels.push(timestamp);
    trafficChart.data.datasets[0].data.push(data.download);
    trafficChart.data.datasets[1].data.push(data.upload);
    
    // 최대 20개 데이터 포인트 유지
    if (trafficChart.data.labels.length > 20) {
        trafficChart.data.labels.shift();
        trafficChart.data.datasets[0].data.shift();
        trafficChart.data.datasets[1].data.shift();
    }
    
    trafficChart.update();
    
    // 총 트래픽 업데이트
    totalTrafficDown += data.download;
    totalTrafficUp += data.upload;
    document.getElementById('download-traffic').textContent = formatTrafficSize(totalTrafficDown);
    document.getElementById('upload-traffic').textContent = formatTrafficSize(totalTrafficUp);
    
    // 속도 기록 업데이트
    const currentSpeed = data.download + data.upload;
    speedHistory.push(currentSpeed);
    if (speedHistory.length > 100) speedHistory.shift();
    
    // 최대 속도 업데이트
    if (currentSpeed > maxSpeed) {
        maxSpeed = currentSpeed;
        document.getElementById('max-speed').textContent = formatTrafficSize(maxSpeed) + '/s';
    }
    
    // 평균 속도 업데이트
    const avgSpeed = calculateAvgSpeed();
    document.getElementById('avg-speed').textContent = formatTrafficSize(avgSpeed) + '/s';
    
    // 패턴 차트 업데이트
    const hour = new Date().getHours();
    patternChart.data.datasets[0].data[hour] += currentSpeed;
    patternChart.update();
});

// 소켓 이벤트: MAC 주소 업데이트
socket.on('mac_update', function(data) {
    if (data.mac_dict && data.mac_dict[ip]) {
        document.getElementById('mac-address').textContent = data.mac_dict[ip];
    }
});

// 소켓 이벤트: 호스트명 업데이트
socket.on('hostname_update', function(data) {
    if (data.ip === ip) {
        document.getElementById('hostname').textContent = data.hostname || 'Unknown';
    }
});

// 소켓 이벤트: 프로토콜 통계
socket.on('protocol_stats', function(data) {
    if (data.ip !== ip) return;
    
    protocolChart.data.datasets[0].data = [
        data.tcp || 0,
        data.udp || 0,
        data.icmp || 0,
        data.other || 0
    ];
    protocolChart.update();
});

// 소켓 이벤트: 포트 통계
socket.on('port_stats', function(data) {
    if (data.ip !== ip) return;
    
    const ports = Object.keys(data.ports).slice(0, 10);
    const counts = ports.map(port => data.ports[port]);
    
    portChart.data.labels = ports;
    portChart.data.datasets[0].data = counts;
    portChart.update();
});

// 소켓 이벤트: 패킷 로그
socket.on('packet_log', function(data) {
    if (data.ip !== ip) return;
    
    packetLog.unshift(data.packet);
    if (packetLog.length > 100) packetLog.pop();
    
    renderPacketLog();
});

// 소켓 이벤트: 스트리밍 서비스 감지
socket.on('streaming_detection', function(data) {
    if (data.ip !== ip || !data.services || data.services.length === 0) return;
    
    const container = document.getElementById('streaming-services');
    container.innerHTML = '';
    
    data.services.forEach(service => {
        const serviceCard = document.createElement('div');
        serviceCard.className = `streaming-card app-${service.toLowerCase()}`;
        serviceCard.innerHTML = `
            <div class="streaming-icon">
                <i class="fas fa-video"></i>
            </div>
            <div class="streaming-name">${service}</div>
        `;
        container.appendChild(serviceCard);
    });
});