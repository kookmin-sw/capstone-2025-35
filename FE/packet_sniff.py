from scapy.all import sniff, IP, TCP, UDP, ARP, Ether, srp
from collections import defaultdict
from dotenv import load_dotenv
import os
import threading
import time
import platform
import pickle

load_dotenv()

#파라미터
MIN_PACKET_COUNT = 100
UPDATE_MAC_INTERVAL = 10

MONITORING_IP = os.getenv('MONITORING_IP', '')
MONITORING_IP_SET = set(ip.strip() for ip in MONITORING_IP.split(','))
MONITORING_MAC_DICT = {}

def get_mac_from_arp_cache(ip):
    """OS의 ARP 캐시에서 특정 IP의 MAC 주소를 가져옴"""
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

def update_mac_address():
    """주기적으로 MONITORING_IP의 MAC 주소를 업데이트"""
    while True:
        for ip in MONITORING_IP_SET:
            MONITORING_MAC_DICT[ip] = get_mac_address(ip) or "Unknown"
        time.sleep(UPDATE_MAC_INTERVAL)

# MAC 주소 업데이트 스레드 시작
def start_mac_address_thread():
    mac_update_thread = threading.Thread(target=update_mac_address, daemon=True)
    mac_update_thread.start()

#4-tuple을 키로 하는 패킷 길이 딕셔너리 생성
packet_size_dict = defaultdict(list)

def get_packet_direction(src_ip, dst_ip):
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

def process_packet(packet):
    """실시간 패킷 스니핑"""
    if IP in packet:
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        direction = get_packet_direction(src_ip, dst_ip)

        if direction is None:
            return  # 모니터링하지 않는 트래픽은 무시
        
        src_port, dst_port = get_ports(packet)
        
        if direction == 'inbound':
            src_ip, dst_ip = dst_ip, src_ip
            src_port, dst_port = dst_port, src_port
        
        mac_address = MONITORING_MAC_DICT.get(src_ip, "Unknown")

        four_tuple = (mac_address, src_ip, src_port, dst_ip, dst_port)
        packet_size = len(packet) * (-1 if direction == 'outbound' else 1)  # outbound면 음수 변환

        packet_size_dict[four_tuple].append(packet_size)
        if len(packet_size_dict[four_tuple]) > MIN_PACKET_COUNT:
            print(f"{four_tuple}: {sum(packet_size_dict[four_tuple])}")

if __name__ == '__main__':
    # BPF 필터를 이용하여 특정 IP만 감시
    filter_str = " or ".join(f"host {ip}" for ip in MONITORING_IP_SET)
    start_mac_address_thread()
    time.sleep(UPDATE_MAC_INTERVAL)
    sniff(prn=process_packet, filter = filter_str)
    