from scapy.all import ARP, Ether, srp, TCP, UDP
import os
import time
import platform

def get_mac_from_arp_cache(ip):
    """
    OS의 ARP 캐시에서 특정 IP의 MAC 주소를 가져옴
    macOS만 시도하여 추가 실험 필요
    """
    os_type = platform.system()
    if os_type == "Darwin":
        output = os.popen(f"arp -n {ip}").read()
        if "no entry" in output:
            return None
        return output.split()[3]
    elif os_type == "Linux":
        output = os.popen(f"ip neigh show {ip}").read()
        if "FAILED" in output:
            return None
        return output.split()[4]
    elif os_type == "Windows":
        output = os.popen(f"arp -a {ip}").read()
        if "No ARP Entries Found." in output:
            return None
        return output.split()[3].replace('-', ':')
    
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