const socket = io.connect("http://localhost:5002");
const charts = {};  // IP별 차트 저장
const chartContainers = {}; // IP별 차트 컨테이너 저장
let macDict = {}; // MAC 주소 저장용 객체
let maxSize = 80000
let period = 20

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

socket.on("traffic_total", function (data) {
    let secondsPassed = data.seconds_passed;
    let trafficData = data.traffic_total;

    Object.keys(trafficData).forEach((ip) => {
        if (!charts[ip]) {
            createChart(ip);
        }

        let chart = charts[ip];
        let label = Math.max(0, secondsPassed - period - 1) + chart.data.labels.length;
        let val = Math.min(Math.max(0, trafficData[ip].length - period - 1) + chart.data.labels.length, period - 1);
        console.log(label)
        while (label < secondsPassed) {
            chart.data.labels.push(label++);
            chart.data.datasets[0].data.push(trafficData[ip][val++]);
        }
        while (chart.data.labels.length > period) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }

        chart.update('none');
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
                label: "트래픽 (bytes)",
                data: [],
                borderColor: `hsl(${Object.keys(charts).length * 60}, 100%, 50%)`,
                borderWidth: 2,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: "경과 시간 (초)"
                    },
                    min: 0,
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: "트래픽량 (bytes)"
                    },
                    beginAtZero: true
                }
            }
        }
    });
}