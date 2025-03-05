const socket = io.connect("http://localhost:5002");
const charts = {};  // IP별 차트 저장
const chartContainers = {}; // IP별 차트 컨테이너 저장
let macDict = {}; // MAC 주소 저장용 객체

// Chart.js Zoom 플러그인 등록
Chart.register(ChartZoom);

// 표 동적 생성 (처음 한 번만 실행)
function createTable() {
    let tableContainer = document.createElement("div");
    tableContainer.className = "table-container"; // CSS 스타일 적용용 div
    tableContainer.innerHTML = `
        <table class="traffic-info-table">
            <thead>
                <tr>
                    <th>IP 주소</th>
                    <th>MAC 주소</th>
                    <th>트래픽 그래프</th>
                    <th>상세보기</th>
                </tr>
            </thead>
            <tbody id="table-body"></tbody>
        </table>
    `;
    document.getElementById("charts").before(tableContainer);
}

// 새로운 IP 행 추가
function addRow(ip) {
    let tableBody = document.getElementById("table-body");

    let row = document.createElement("tr");
    row.innerHTML = `
        <td>
            <a href="/traffic/${ip}" class="ip-link">${ip}</a>
        </td>
        <td id="mac-${ip}">Loading...</td>
        <td id="chart-container-${ip}"></td>
        <td>
            <button onclick="goToDetail('${ip}')" class="detail-btn">상세 보기</button>
        </td>
    `;
    tableBody.appendChild(row);
}

// 상세 페이지 이동 함수
function goToDetail(ip) {
    window.location.href = `/traffic/${ip}`;
}

// MAC 주소 업데이트 이벤트 리스너 추가
socket.on("update_mac", function(macData) {
    let [src_ip, src_mac] = macData;
    macDict[src_ip] = src_mac;
    console.log(macDict);
    updateMacUI(src_ip);
});

// 트래픽 업데이트 이벤트 리스너 수정 (스크롤 가능하게 변경)
socket.on("update_traffic", function(data) {
    let now = new Date().toLocaleTimeString();

    Object.keys(data).forEach((ip) => {
        if (!charts[ip]) {
            createChart(ip);
        }

        let chart = charts[ip];

        // X축(시간) 데이터 추가
        chart.data.labels.push(now);

        // Y축(트래픽) 데이터 추가
        chart.data.datasets[0].data.push(data[ip]);

        // 최대 20개까지만 유지 (스크롤 가능)
        if (chart.data.labels.length > 20) {
            chart.options.scales.x.min++;
            chart.options.scales.x.max++;
        }

        chart.update();

        // MAC 주소 UI 업데이트
        updateMacUI(ip);
    });
});

// 차트 생성
function createChart(ip) {
    if (!document.getElementById("table-body")) {
        createTable();
    }

    addRow(ip);

    let container = document.createElement("div");
    container.className = "chart-wrapper";
    container.innerHTML = `<canvas id="chart-${ip}"></canvas>`;

    document.getElementById(`chart-container-${ip}`).appendChild(container);

    let ctx = document.getElementById(`chart-${ip}`).getContext("2d");

    charts[ip] = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                data: [],
                borderColor: `hsl(${Object.keys(charts).length * 60}, 100%, 50%)`,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                zoom: {
                    pan: {
                        enabled: true, // 마우스로 패닝 가능
                        mode: "x",
                    },
                    zoom: {
                        wheel: {
                            enabled: true, // 마우스 휠로 줌 가능
                        },
                        pinch: {
                            enabled: true, // 터치 줌 가능
                        },
                        mode: "x",
                    },
                }
            },
            scales: {
                x: {
                    display: true,
                    min: 0,
                    max: 20,
                },
                y: {
                    display: true,
                    beginAtZero: true
                }
            }
        }
    });

    // MAC 주소 UI 업데이트
    updateMacUI(ip);
}

// MAC 주소 UI 업데이트 함수 추가
function updateMacUI(ip) {
    if (document.getElementById(`mac-${ip}`)) {
        document.getElementById(`mac-${ip}`).textContent = macDict[ip] || "Unknown";
    }
}