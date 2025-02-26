from scapy.all import ARP, Ether, srp, TCP, UDP
import subprocess
import platform

def get_mac_from_arp_cache(ip):
    """
    OS의 ARP 캐시에서 특정 IP의 MAC 주소를 가져옴
    macOS, Linux, Windows 지원
    """
    os_type = platform.system()
    
    try:
        if os_type == "Darwin":
            result = subprocess.run(["arp", "-n", ip], capture_output=True, text=True, check=True)
            output = result.stdout
            if "no entry" in output:
                return None
            return output.split()[3]  # MAC 주소 추출
        
        elif os_type == "Linux":
            result = subprocess.run(["arp", "-a", ip], capture_output=True, text=True, check=True)
            output = result.stdout
            if "no match found" in output:
                return None
            return output.split()[3]  # MAC 주소 추출
        
        elif os_type == "Windows":
            result = subprocess.run(["arp", "-a", ip], capture_output=True, text=True, check=True)
            output = result.stdout
            if "No ARP Entries Found." in output:
                return None
            return output.split()[3].replace('-', ':')  # Windows MAC 형식 변환
        
    except subprocess.CalledProcessError:
        return None  # 오류 발생 시 None 반환

    return None  # MAC 주소를 찾지 못한 경우

def get_mac_address(ip):
    """ARP 캐시에서 MAC 주소를 우선 조회하고, 없으면 ARP 요청 실행"""
    mac = get_mac_from_arp_cache(ip)
    if mac:
        return mac  # 캐시에서 발견된 MAC 주소 반환

    # 캐시에 없으면 ARP 요청 실행
    arp_request = ARP(pdst=ip)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp_request

    ans = srp(packet, timeout=2, verbose=False)[0]

    if ans:
        return ans[0][1].hwsrc
    return None

def get_packet_direction(src_ip, dst_ip, MONITORING_IP_SET):
    """패킷 방향을 판단하는 함수"""
    if src_ip not in MONITORING_IP_SET and dst_ip not in MONITORING_IP_SET:
        return None  # 모니터링 대상이 아닌 경우
    if src_ip in MONITORING_IP_SET and dst_ip in MONITORING_IP_SET:
        return None  # 모니터링 IP 간 통신 무시
    return 'outbound' if src_ip in MONITORING_IP_SET else 'inbound'

def get_ports(packet):
    """패킷에서 포트 정보를 추출하는 함수"""
    if TCP in packet:
        return packet[TCP].sport, packet[TCP].dport
    if UDP in packet:
        return packet[UDP].sport, packet[UDP].dport
    return 0, 0