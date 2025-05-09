# demo.js 명세서

## 개요
`demo.js`는 실시간 트래픽 모니터링 시스템의 정적 데모 페이지에서 사용되는 JavaScript 파일입니다. 이 파일은 실제 데이터 없이 UI 디자인을 보여주는 데모 페이지의 상호작용 기능을 제공합니다.

## 주요 기능

### 1. 탭 전환 기능
- 메인 페이지와 상세 페이지 간의 탭 전환 기능 제공
- 사용자가 탭을 클릭하면 해당 콘텐츠를 표시하고 다른 콘텐츠는 숨김

### 2. 어바웃 정보 표시
- 어바웃 링크 클릭 시 시스템에 대한 간략한 정보를 알림창으로 표시

## 함수 목록

### `showTab(tabName)`
- 목적: 선택한 탭의 콘텐츠를 표시하고 다른 탭의 콘텐츠는 숨김
- 매개변수:
  - `tabName` (string): 표시할 탭 이름 ('main' 또는 'detail')
- 동작:
  1. 모든 탭과 콘텐츠를 비활성화
  2. 선택한 탭과 해당 콘텐츠를 활성화

## 이벤트 핸들러

### 페이지 로드 시 초기화
- 어바웃 링크에 클릭 이벤트 리스너 등록

### 어바웃 링크 클릭 이벤트
- 클릭 시 기본 동작 방지 (preventDefault)
- 시스템에 대한 정보를 알림창으로 표시

## 사용 방법

1. HTML 파일에 스크립트 포함:
```html
<script src="js/demo.js"></script>
```

2. HTML에 필요한 요소 포함:
   - 탭 전환을 위한 요소 (class="demo-tab")
   - 탭 콘텐츠를 표시할 요소 (class="demo-content")
   - 어바웃 링크 (id="about-link")

3. 탭 전환 함수 호출:
```html
<div class="demo-tab" onclick="showTab('main')">메인 페이지</div>
<div class="demo-tab" onclick="showTab('detail')">상세 페이지</div>
```

## HTML 구조 요구사항

### 탭 구조
```html
<div class="demo-tabs">
    <div class="demo-tab active" onclick="showTab('main')">메인 페이지</div>
    <div class="demo-tab" onclick="showTab('detail')">상세 페이지</div>
</div>
```

### 콘텐츠 구조
```html
<div id="main-demo" class="demo-content active">
    <!-- 메인 페이지 콘텐츠 -->
</div>
<div id="detail-demo" class="demo-content">
    <!-- 상세 페이지 콘텐츠 -->
</div>
```

### 어바웃 링크
```html
<a href="#" id="about-link">About</a>
```

## CSS 클래스 설명

### 탭 관련 클래스
- `.demo-tab`: 탭 버튼 스타일
- `.demo-tab.active`: 활성화된 탭 스타일

### 콘텐츠 관련 클래스
- `.demo-content`: 탭 콘텐츠 스타일 (기본적으로 숨김)
- `.demo-content.active`: 활성화된 콘텐츠 스타일 (표시됨)

## 참고 사항
- 이 스크립트는 정적 데모 페이지에서만 사용됩니다.
- 실제 데이터를 포함한 동적 데모를 보려면 `python BE/demo.py` 명령어를 실행한 후 http://localhost:5002에 접속해야 합니다.