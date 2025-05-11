/**
 * 데모 페이지 스크립트
 * 
 * 이 스크립트는 실시간 트래픽 모니터링 시스템의 UI 디자인을 보여주는 정적 데모 페이지에서 사용됩니다.
 * 실제 데이터는 포함되어 있지 않으며, 백엔드 연동 없이 UI만 확인할 수 있습니다.
 */

/**
 * 탭 전환 함수
 * 
 * @param {string} tabName - 표시할 탭 이름 ('main' 또는 'detail')
 */
function showTab(tabName) {
    // 모든 탭 비활성화
    document.querySelectorAll('.demo-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 모든 콘텐츠 숨기기
    document.querySelectorAll('.demo-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // 선택한 탭 활성화
    if (tabName === 'main') {
        document.querySelector('.demo-tab:nth-child(1)').classList.add('active');
        document.getElementById('main-demo').classList.add('active');
    } else {
        document.querySelector('.demo-tab:nth-child(2)').classList.add('active');
        document.getElementById('detail-demo').classList.add('active');
    }
}

// 페이지 로드 시 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', function() {
    // 어바웃 링크 클릭 이벤트
    document.getElementById('about-link').addEventListener('click', function(e) {
        e.preventDefault();
        alert('실시간 트래픽 모니터링 시스템\n\n네트워크 트래픽을 실시간으로 모니터링하고 분석하는 시스템입니다.\n스트리밍 서비스 감지 및 트래픽 패턴 분석 기능을 제공합니다.');
    });
});