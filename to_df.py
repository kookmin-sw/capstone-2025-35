import pyshark
import pandas as pd
from scapy.all import rdpcap, IP
from collections import OrderedDict
import os
import numpy as np
from pathlib import Path
from tqdm.auto import tqdm
import subprocess
import re


def int_2_prot(key):
    tmp_dict = {
        1: "ICMP",
        2: "IGMP",
        4: "IPencap",
        6: "TCP",
        17: "UDP"
    }

    return tmp_dict[key]

class to_df:
    def __init__(self, app_name, data_path):
        self.app_name = app_name
        self.data_path = data_path
        self.sessions = OrderedDict()
        self.initial_ips = {}
        self.sni = {}
        self.cname = {}

    def get_sni(self):
        cap = pyshark.FileCapture(str(self.data_path), display_filter='tls.handshake.extensions_server_name')
        for pkt in cap:
            if hasattr(pkt, 'tls'):
                if hasattr(pkt.tls, 'handshake_extensions_server_name'):
                    dst_ip = pkt.ip.dst
                    sni = pkt.tls.handshake_extensions_server_name
                    self.sni[dst_ip] = sni
        cap.close()
    
    def get_cname(self):
        cap = pyshark.FileCapture(str(self.data_path), display_filter='dns')
        for pkt in cap:
            if hasattr(pkt, 'dns'):
                if hasattr(pkt.dns, 'cname'):
                    cname = pkt.dns.cname
                    if hasattr(pkt.dns, 'a'):
                        dst_ip = pkt.dns.a
                        self.cname[dst_ip] = cname
        cap.close()
    
    def nslookup(self, ip):
        try:
            result = subprocess.run(["nslookup", ip], capture_output=True, text=True, check=True)
            output = result.stdout

            # "name =" 패턴을 찾아서 도메인 이름만 추출
            match = re.search(r"name\s*=\s*([\w\.-]+)", output, re.IGNORECASE)
            if match:
                return match.group(1)  # 도메인 이름만 반환
            else:
                return "No name found"
        except subprocess.CalledProcessError as e:
            return None

    def pcap_2_df(self, duplicate = False):
        # PCAP 폴더 이후의 경로를 유지하며 CSV 저장 경로 설정
        relative_path = self.data_path.parts[:-5]
        app_name, device, network, filename = self.data_path.parts[-4:]
        csv_path = Path(*relative_path) / Path("csv")

        # CSV 저장 폴더 생성
        csv_path.mkdir(parents=True,exist_ok=True)

        # CSV 파일 경로 설정
        csv_file_path = csv_path / app_name / device / network / filename.replace(".pcap", ".csv")
        if csv_file_path.exists() and not duplicate:
            print(f"[INFO] {csv_file_path} already exists.")
            return
        
        self.data_path = str(self.data_path)
        self.get_sni()
        if self.app_name == "Youtube":
            self.get_cname()
        packets = tqdm(rdpcap(self.data_path))   

        for idx, pkt in enumerate(packets):
            if 'IP' not in pkt:
                continue
        
            ip_layer = pkt['IP']
            protocol = str(ip_layer.proto)

            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
        
            src_port = str(pkt.sport) if hasattr(pkt, 'sport') else None
            dst_port = str(pkt.dport) if hasattr(pkt, 'dport') else None

            try:
                session_key = '_'.join([src_ip, src_port, dst_ip, dst_port, protocol])
                reversed_key = '_'.join([dst_ip, dst_port, src_ip, src_port, protocol])
            except TypeError as e:
                session_key = '_'.join([src_ip, "0", dst_ip, "0", protocol])
                reversed_key = '_'.join([dst_ip, "0", src_ip, "0", protocol])
            
            if session_key in self.sessions:
                pass
            elif reversed_key in self.sessions:
                session_key = reversed_key
            else:
                self.initial_ips[session_key] = (src_ip, dst_ip)
                if protocol == '6':
                    sni = self.sni.get(dst_ip, None)
                elif protocol == '17':
                    sni = self.cname.get(dst_ip, None)
                    if sni is None:
                        sni = self.nslookup(dst_ip)
                else:
                    sni = None
                
                if sni is None:
                    sni = "No SNI"     
                self.sessions[session_key] = {'sni': sni, 'data': [], 'timestamps': [0], 'directions': []}

            
            current_session = self.sessions[session_key]['data']
            ip1, ip2 = self.initial_ips[session_key]
            direction = '-' if src_ip == ip1 else  '+'

            packet_size = 0
            if pkt.haslayer("TCP"):
                packet_size = len(bytes(pkt["TCP"].payload))
            elif pkt.haslayer("UDP"):
                packet_size = len(bytes(pkt["UDP"].payload))
            else:
                continue
            
            current_session += [f'{direction}{packet_size}'] if 0 <= packet_size <= 1600 else []
            
            current_timestamps = self.sessions[session_key]['timestamps']
            current_time = max(current_timestamps[-1], float(pkt.time))
            current_timestamps += [current_time]

            current_directions = self.sessions[session_key]['directions']
            current_direction = -1 if direction == "-" else +1
            current_directions += [current_direction]

        df_data = []
        
        for key in self.sessions.keys():
            data = self.sessions[key]
            splt = data['data']
            key = key.split("_")
            sni = data['sni']
            iat = data['timestamps']
            d = data['directions']
            splt_arr = np.array([int(x) for x in splt])

            df_data.append([
                *key[:4], int_2_prot(int(key[4])), 
                len(splt_arr[splt_arr>0]), 
                len(splt_arr[splt_arr<0]), 
                int(sum(splt_arr[splt_arr>0])), 
                int(sum(splt_arr[splt_arr<0])), 
                len(splt), 
                splt,
                sni,
                [x - iat[1] for x in iat[1:]],
                d
            ])

        df = pd.DataFrame(
            df_data, columns=['Source IP', 'Source Port', 'Destination IP', 'Destination Port', 'Protocol', 'Rx-Pkts','Tx-Pkts', 'Rx-Bytes', 'Tx-Bytes', "SPLT-Len", "SPLT-Data", "SNI", "IAT-Data", "Direction-Data"]
        ).sort_values(by=['Rx-Bytes'], axis=0, ascending=False)

        name = os.path.split(self.data_path)[1]
        print(f'[INFO] df will be saved at ===>', csv_file_path)
                
        df.to_csv(csv_file_path, index=False)

        return df

if __name__ == "__main__":
    pcap_folder = Path("pcap")
    pcap_files = list(pcap_folder.glob("**/*.pcap"))

    valid_devices = {"Phone", "PC"}
    valid_networks = {"WiFi", "Ethernet", "LTE"}
    valid_filenames = {"MIN", "PARK", "SEO", "JANG", "JEON"}

    for pcap_file in pcap_files:
        parts = pcap_file.parts
        if len(parts) < 4:
            print(f"[ERROR] 부적절한 않은 폴더구조: {pcap_file}. 다음과 같이 작성해주세요: 어플리케이션이름/Device/Network/File.pcap")
            exit(1)

        app_name, device, network, filename = parts[-4], parts[-3], parts[-2], parts[-1]

        if device not in valid_devices:
            print(f"[ERROR] 부적절한 디바이스 폴더 이름: '{device}' in {pcap_file}. 다음과 같이 바꿔주세요: {valid_devices}")
            exit(1)

        if network not in valid_networks:
            print(f"[ERROR] 부적절한 인터넷 이름: '{network}' in {pcap_file}. 다음과 같이 바꿔주세요: {valid_networks}")
            exit(1)
        
        filename = filename.upper()
        for valid_filename in valid_filenames:
            if valid_filename in filename:
                break
        else:
            print(f"[ERROR] 부적절한 파일 이름: '{filename}' in {pcap_file}. 다음과 같이 바꿔주세요: {valid_filenames}")
            exit(1)

        print(f"[INFO] Processing {pcap_file}")

        todf = to_df(app_name, pcap_file)
        todf.pcap_2_df(duplicate=True)