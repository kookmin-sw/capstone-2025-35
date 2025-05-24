# 어플리케이션 차단 기능(MacOS, Apple Silicon 기준)

상세 페이지에 들어가면, 탐지된 어플리케이션 옆에 **차단** 버튼이 있습니다.  

이를 클릭하면 다음과 같이 처리합니다.  

1. 가장 최근에 탐지된 패킷의(threshold 이상) 5-tuple 을 이용해 **pf** 의 rule 을 만들어서 차단합니다.  
2. **suricata** 에 후속으로 연결되는 동적 IP 를 차단하기 위해 **SNI** 를 기반으로 로그를 만들고, 이를 기반으로 **pf** rule 을 만들어서 차단합니다.

# 설정 방법

## 참고사항

우선 제가 사용하는 노트북은 Apple Silicon 을 사용하고 있어서, Intel 맥북은 **경로가 다를 수 있습니다.**  

그리고 차단 기능을 넣으면서, 한 가지 유의사항이 생겼습니다.  

sudo 권한이 있어야 pf rule 을 설정할 수 있으므로, app.py 를 실행할 때 **sudo** 로 실행해야 합니다.  

```bash
cd BE
sudo python3 app.py
```

그리고 **탐지한 어플리케이션과 실제 어플리케이션이 같을 때만** 차단 버튼을 눌러주세요!!  

그렇지 않으면, suricata 에 다른 rule 이 들어가서 차단을 할 수 없습니다.  

## 0. homebrew 설치

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

위의 명령을 입력해서 homebrew 를 설치합니다.  

설치하면, 터미널에 환경 변수를 설정하기 위해 입력해야하는 명령어를 알려줍니다.  

아래의 명령과 비슷한 형식이지만, 약간의 차이점이 있을 수 있음(Intel Mac, Apple Silicon)

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

그리고 homebrew 버전 확인을 통해 설치를 확인합니다.  

```bash
brew --version
```

## 1. Homebrew 로 suricata 설치

```bash
brew install suricata
```

터미널에서 위의 명령어를 입력해서 **suricata 를 설치**합니다.


## 2. suricata.yaml 설정

```bash
/opt/homebrew/etc/suricata/suricata.yaml

# 혹은

/usr/local/etc/suricata/suricata.yaml
```

suricata 의 설정 파일인 **suricata.yaml** 의 설정을 수정해야 합니다.  

```yaml
# Linux high speed capture support
af-packet:
  - interface: en0

...

# Cross platform libpcap capture support
pcap:
  - interface: en0

...

pfring:
  - interface: en0
```

위처럼 **인터페이스를 환경에 맞게 수정**해야합니다.("interface:" 를 검색해서 바꿔주세요.)  

저는 위처럼 3개만 en0 으로 바꿨는데, 동작합니다.(af-packet 만 수정해도 동작할 수 있습니다.)  

```yaml
# 아래의 경로는, rule 이 있는 경로로 바꿔야함
default-rule-path: /opt/homebrew/var/lib/suricata/rules

rule-files:
  #- suricata.rules <- 기본 suricata rule(사용 X, 주석 상관없음)

  # 이 프로그램에서 생성한 rule 을 넣을 파일
  - capstone.rules
```

약 2180번째 줄에 다음과 같은 **rule 경로 설정**하는 곳을 위와 같은 형식으로 수정해야 합니다.  

## 3. capstone.rules 생성

위의 **default-rule-path** 에 **capstone.rules** 를 생성합니다.  

1. suricata.rules 를 복사해서 만드는 방법
2. vim 등으로 만드는 방법

그리고 잘 동작하는지 테스트 하기 위해 capstone.rules 에 다음과 같은 rule 을 적고 저장합니다.  

```text
alert tls any any -> any any (msg:"[ALERT] NAVER VOD streaming detected(pstatic)"; tls.sni; content:"-vod."; nocase; tls.sni; content:".pstatic.net"; nocase; sid:7000001; rev:1;)
#alert tls any any -> any any (msg:"[ALERT] NAVER VOD streaming detected(NEW)"; tls.sni; content:"-vod.pstatic.net"; nocase; sid:7000001; rev:1;)
alert tls any any -> any any (msg:"[ALERT] NAVER VOD streaming detected(smartmediarep)"; tls.sni; content:"smartmediarep.com"; nocase; sid:7000002; rev:1;)
```

위의 rule 은 SNI 가 **navertv** 스트리밍 서비스인 패킷에 대해 로그를 남기는 rule 입니다.  

rule 을 작성하고 저장한 후에, 아래의 명령을 통해 suricata 를 실행하면 됩니다.  

```bash
# sudo suricata -c [suricata.yaml 경로] -c
sudo suricata -c /opt/homebrew/etc/suricata/suricata.yaml -i en0
```

그리고 터미널에서 다음과 같은 명령을 입력해서 **fast.log** 를 실시간으로 켜놓습니다.  

```bash
tail -f /opt/homebrew/var/log/suricata/fast.log
```

또는

```bash
tail -f /usr/local/var/log/suricata/fast.log
```

그 다음에 navertv 에 들어가서 영상을 누르면, **fast.log** 에 suricata 로그가 탐지되는 것을 확인할 수 있습니다.  

## 4. pf.conf 설정 및 capstone anchor 만들기

```bash
/etc/pf.conf
```

위의 경로에서 pf 방화벽의 설정파일인 **pf.conf** 를 수정해야 합니다.  

```bash
sudo vim /etc/pf.conf
```

위의 명령으로 파일 가장 아래에 다음과 같은 2줄을 추가해야 합니다.  

```bash
anchor "capstone"
load anchor "capstone" from "/etc/pf.anchors/capstone"
```

pf 에는 rule 을 모아서 관리할 수 있는 **ancher** 라는 기능이 있습니다.  

그래서 ``/etc/pf.anchors`` 경로에 capstone 을 만들어서(기존에 com.apple 을 복사하는 등) app.py 에서 규칙을 추가할 예정입니다.  

pf.conf 를 수정하고 저장합니다.  

## 5. pf 방화벽 활성화 및 설정 적용

```bash
# pf 방화벽 활성화
sudo pfctl -e

# pf.conf 파일 로드 및 적용
sudo pfctl -f /etc/pf.conf
```

위의 명령을 통해 pf 방화벽을 활성화하고, 4번에서 설정한 pf.conf 를 적용해야 합니다.  

```bash
sudo pfctl -sr
```

그리고 위의 명령을 통해 다음과 같이 capstone 이 적용되었는지 확인해야 합니다.  

```bash
anchor "com.apple/*" all
anchor "capstone" all
```

위와 같은 결과가 나오면 잘 적용된 것입니다.  

# 코드 주요 부분

## 1. app.py

```python
@socketio.on('get_detected_sessions') 
def handle_get_detected_sessions():
    print(f"[INFO] app.py -> get_detected_sessions 호출")
    sniffer.send_detected_sessions()
```

위의 함수는 traffic_detail.js 에서 차단 버튼을 눌렀을 때, 다시 traffic_detail.js 로 **5-tuple 을 요청**하는 함수입니다.  
-> (차단 버튼 클릭 -> traffic_detail.js(요청) -> app.py(요청) -> traffic_detail.js(데이터 전송) -> app.py(rule 추가))  

```python
# 아래의 경로는 환경에 따라 수정해야함
# pf 에서 사용할 앵커 이름 및 경로와 아래에서 사용할 suricata 로그 경로
# /etc/pf.anchors/capstone 에 접근하려면 root 권한이 있어야해서
# 이 코드를 실행할 때 sudo 를 붙여야함
ANCHOR_NAME = "capstone"
ANCHOR_FILE = f"/etc/pf.anchors/{ANCHOR_NAME}"
EVE_LOG_PATH = "/opt/homebrew/var/log/suricata/eve.json"

# Suricata 규칙 파일 경로, YAML 파일 및 SID(고유 식별자)
SURICATA_RULES_PATH = "/opt/homebrew/var/lib/suricata/rules/capstone.rules"
SURICATA_YAML_PATH = "/opt/homebrew/etc/suricata/suricata.yaml"
SID = 1000001  
```

위의 코드는 주석에 있는 것처럼 app.py 에서 차단하기 위해 사용하는 **파일 경로 및 이름**입니다.  

위의 경로는 **환경에 따라 수정**해야 합니다.  

```python
# 어플리케이션 및 SNI 매핑
# BitTorrent 가 없음
# 또한 몇 개의 어플리케이션을 추가해야할 수 있음
APP_SNI = {
    "youtube": "googlevideo.com",
    "youtube_tls": "googlevideo.com",
    "netflix": ["nflxvideo.net", "nflxso.net", "ftl.netflix.com"],
    "navertv": ["vod.pstatic.net", "smartmediarep.com", "vod.akamaized.net", "livecloud.pstatic.net", "livecloud-thumb.akamaized.net"],
    "wavve": ["vod.cdn.wavve.com", "qvod.cdn.wavve.com", "live.cdn.wavve.com", "flive.cdn.wavve.com"],
    "coupangplay": "coupangstreaming.com",
    "instagram": "fbcdn.net",
    "instagram_tls": "fbcdn.net",
    "steam": ["steambroadcast.akamaized.net", "video-manager.steamstatic.com", "steamcontent.com"],
    "soop": "live.sooplive.co.kr",
}
```

suricata 에서 규칙을 만들 때, 사용할 **각 어플리케이션의 SNI** 입니다.  

```python
# 앵커를 pf 에 로드하는 명령
# pfctl -a capstone -f /etc/pf.anchors/capstone : capstone 파일에서 rule 을 읽어와서 PF 에 적용
def reload_anchor():
    result = subprocess.run(["sudo", "pfctl", "-a", ANCHOR_NAME, "-f", ANCHOR_FILE], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(result.stderr)
```

위의 함수는 **pf 에 규칙을 추가하고 이를 pf 에 적용**하는 함수입니다.  

```python
def block_ip(src_ip, dst_ip)
```

위의 함수은 **출발지, 도착지 IP 을 이용해 양방향 차단**을 하는 함수입니다.  

```python
def monitor_suricata_logs()
```

위의 함수는 suricata 를 실행하면서, suricata 의 로그 파일 중 하나인 **eve.json** 에 탐지된 5-tuple 을 이용해 pf 에 rule 을 추가하는 함수입니다.  

```python
def is_suricata_running()
def restart_suricata()
```

위의 함수는 각각 현재 suricata 가 실행 중인지 확인하는 함수이고, suricata 를 재실항하는 함수입니다.(**suricata 에 rule 을 추가**하거나 차단된 IP 를 전부 **해제**할 때 사용)

```python
def add_suricata_rule(src_ip, dst_ip, app_name)
```

위의 함수는 출발지, 도착지 IP, 탐지된 어플리케이션 이름으로 **SNI 를 기반으로 로그를 남기는 suricata rule 을 추가**하는 함수입니다.(동적 IP 로 서버 IP 가 변경되어도 차단하기 위해)

```python
@socketio.on('block_streaming_service') 
def block_packet(data)
```

위의 함수는 차단 버튼을 눌렀을 때, **넘겨받은 5-tuple 값으로 위의 함수들을 호출**해서 차단하는 함수입니다.  

```python
@socketio.on('clear_streaming')
def unblock_all_ips()
```

위의 함수는 차단 해제 버튼을 눌렀을 때, **pf, suricata의 rule 을 전부 제거** 하는 함수입니다.  

## 2. traffic_detail.html

```html
        <!-- 스트리밍 서비스 감지 -->
        <div class="analysis-card">
            <h3>스트리밍 서비스 감지</h3>

            <!-- 모든 IP 차단 해제 버튼 임시 삽입 -->
            <button id="clear_block_rule">모든 IP 차단 해제</button>
            <div id="streaming-services" class="streaming-services">
                <div class="no-data">감지된 스트리밍 서비스가 없습니다.</div>
            </div>
        </div>
```

위의 버튼은 **현재 차단된 모든 IP 를 해제**하는 버튼입니다.(임시로 만든 버튼입니다.)  

``app.py 를 실행했다가 종료하기 전에 무조건 눌러주세요.``  

그래야 다음에 실행해서 차단할 때, SID 가 중복되지 않습니다.(이 부분은 더 찾아보겠습니다.)  

## 3. traffic_detail.js

```js
const container = document.getElementById('streaming-services'); //전역 변수로 만든 것 버튼 클릭을 하기 위해
// 소켓 이벤트: 스트리밍 서비스 감지
socket.on('streaming_detection', function(data) {
    if (data.ip !== ip || !data.services || data.services.length === 0) return;
    
    container.innerHTML = '';
    
    data.services.forEach(service => {
        const serviceCard = document.createElement('div');
        serviceCard.className = `streaming-card app-${service.toLowerCase()}`;
        serviceCard.innerHTML = `
        <div class="streaming-content"> 
            <div class="streaming-icon">
                <i class="fas fa-video"></i>
            </div>
            <div class="streaming-name">${service}</div>
        </div>
        <button class="block-btn" data-service="${service}">차단</button>   
    `   ;
        container.appendChild(serviceCard);
    });
});
```

위의 함수는 어플리케이션이 탐지되었을 때, **탐지된 어플리케이션과 차단 버튼**이 나오는 기능입니다.  

```js
// 차단 버튼 클릭 이벤트
container.addEventListener('click', function (e) {
    if (e.target.classList.contains('block-btn')) {
        // 차단 버튼 클릭 시, 서버에 detected_sessions 요청
        socket.emit('get_detected_sessions');
    }
});
```

위의 함수는 차단 버튼을 클릭했을 때, app.py 에 있는 소켓으로 **5-tuple 전송 요청**을 하는 기능입니다.  

```js
// 5-tuple 값 서버로 전달(차단)
socket.on('detected_sessions_update', function(data) {
    const sessions = data.sessions; //sessions -> 5tuple이 포함된 리스트(리스트안에 dic형태로 존재)
    //이 부분에서 서버로부터 sessions dic 형태의 값을 받는다고 보면 됩니다

    socket.emit('block_streaming_service', { sessions: sessions });
});
```

위의 함수는 app.py 에서 **요청받은 데이터를 전송**하는 기능입니다.  

```js
// 차단 해제 버튼 클릭 이벤트
document.getElementById('clear_block_rule').addEventListener('click', function() {
    socket.emit('clear_streaming');
});
```

위의 함수는 차단 해제 버튼을 눌렀을 때, 현재 **capstone, capstone.rules 에 있는 모든 rule 을 제거**하는 기능입니다.  

# 주의사항

차단하는 시나리오가 크게 2가지가 있습니다.  

## 1. 영상 시청 이전에 차단을 누르고 영상 시청하는 경우

이 경우에는 suricata 를 통해 동적 IP 도 차단되기 때문에, **영상 초반에 차단되는 경우**가 많습니다.(혹은 **바로 차단**)  

## 2. 영상 시청 중간에 차단을 누르는 경우

이 경우에는 **바로 차단이 되는 것은 아니고**, 시간이 좀 지나면(약 20초?) 실시간 트래픽 그래프를 같이 보면 다운로드 그래프가 거의 0에 수렴하는 순간부터 더 이상 영상을 받아오지 않습니다.  

이 때, 영상 재생 바에서 회색으로 받아온 이후로 시간을 옮기면 무한로딩에 걸립니다.  