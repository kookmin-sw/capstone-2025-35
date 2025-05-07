# 코드 사용법

**backend.py** 를 ``sudo python3 backend.py`` 로 실행해야 합니다.  
-> **anchor** 에 접근하기 때문에 sudo 명령으로 실행해야 합니다.  

## 작동방식
```
# 네이버 tv
drop tls any any -> any any (msg:"tls 'vod' block"; tls.sni; content:"vod"; sid:2000005; rev:1;)
drop tls any any -> any any (msg:"tls 'smartmedia' block"; tls.sni; content:"smartmedia"; sid:2000006; rev:1;)

# Wavve
drop tls any any -> any any (msg:"tls 'vod' block"; tls.sni; content:"vod"; sid:2000007; rev:1;)

# Netflix
drop tls any any -> any any (msg:"tls 'nflxvideo' block"; tls.sni; content:"nflxvideo"; sid:2000008; rev:1;)

# soop(클립)
drop tls any any -> any any (msg:"tls 'vod' block"; tls.sni; content:"vod"; sid:2000009; rev:1;)

# YouTube
drop tls any any -> any any (msg:"tls 'googlevideo' block"; tls.sni; content:"googlevideo"; sid: 2000010; rev:1;)

# coupangplay
drop tls any any -> any any (msg:"tls 'coupangstreaming' block"; tls.sni; content:"coupangstreaming"; sid: 2000011; rev:1;)
```

위와 같은 rule 을 suricata 의 rule 에 넣습니다.  
그렇게 하고 backend.py 를 실행하면 중간에 **suricata 시작** 버튼이 있습니다.  

버튼을 누르면 그 이후로 발생한 로그의 **서버 IP 를 대상**으로 차단  

일반적으로 입력창은 사용 X  

만약 suricata 를 정지하고 싶으면, **suricata 정지** 를 눌러서 정지할 수 있습니다.  

그 뒤로 원활한 인터넷 사용을 위해 기존에 차단 rule 에 있던 **IP 를 직접 입력해서 차단 해체**를 할 수 있습니다.  