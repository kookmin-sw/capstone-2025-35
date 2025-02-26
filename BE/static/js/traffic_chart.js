const socket = io.connect("http://localhost:5001");
const charts = {};  // IP별 차트 저장
const chartContainers = {}; // IP별 차트 컨테이너 저장
let macDict = {}; // MAC 주소 저장용 객체
let appDict = {}; // 애플리케이션 정보 저장

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
                    <th>앱</th>
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
        <td>${ip}</td>
        <td id="mac-${ip}">Loading...</td>
        <td id="chart-container-${ip}"></td>
        <td id="app-${ip}">-</td>
    `;
    tableBody.appendChild(row);
}

// MAC 주소 업데이트 이벤트 리스너 추가
socket.on("update_mac", function(macData) {
    macDict = macData; // MAC 주소 데이터 저장
    Object.keys(macData).forEach((ip) => updateMacUI(ip)); // UI 업데이트
});

// 트래픽 업데이트 이벤트 리스너 수정 (MAC 주소 포함)
socket.on("update_traffic", function(data) {
    let now = new Date().toLocaleTimeString();

    Object.keys(data).forEach((ip) => {
        if (!charts[ip]) {
            createChart(ip);
        }

        let chart = charts[ip];

        if (chart.data.labels.length > 20) {
            chart.data.labels.shift();
        }
        chart.data.labels.push(now);

        if (chart.data.datasets[0].data.length > 20) {
            chart.data.datasets[0].data.shift();
        }
        chart.data.datasets[0].data.push(data[ip]);

        chart.update();

        // MAC 주소를 UI 업데이트
        updateMacUI(ip);
    });
});

// 애플리케이션 감지 이벤트 리스너 추가
socket.on("app_detect", function(data) {
    const [src_ip, mac_address, app_name] = data;
    console.log(data)

    // IP와 MAC 주소가 일치하는 경우에만 애플리케이션을 등록
    if (macDict[src_ip] === mac_address) {
        appDict[src_ip] = app_name;
        updateAppUI(src_ip);
    }
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
                legend: { display: false }
            },
            scales: {
                x: { display: false },
                y: { display: false , beginAtZero: true }
            }
        }
    });

    // MAC 주소 및 애플리케이션 UI 업데이트
    updateMacUI(ip);
    updateAppUI(ip);
}

// MAC 주소 UI 업데이트 함수 추가
function updateMacUI(ip) {
    if (document.getElementById(`mac-${ip}`)) {
        document.getElementById(`mac-${ip}`).textContent = macDict[ip] || "Unknown";
    }
}

// 애플리케이션 UI 업데이트 함수 추가
function updateAppUI(ip) {
    if (document.getElementById(`app-${ip}`)) {
        document.getElementById(`app-${ip}`).textContent = appDict[ip] || "탐지 중...";
    }
}