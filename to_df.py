import pyshark
import pandas as pd
from scapy.all import rdpcap, IP
from collections import OrderedDict
import os
import numpy as np
from pathlib import Path
from tqdm.auto import tqdm

def int_2_prot(key):
    tmp_dict = {
        1: "ICMP",
        2: "IGMP",
        4: "IPencap",
        6: "TCP",
        17: "UDP"
    }

    return tmp_dict[key]

def pcap_2_df(data_path):
    # PCAP 폴더 이후의 경로를 유지하며 CSV 저장 경로 설정
    relative_path = data_path.relative_to(data_path.parts[0]) # PCAP 폴더 이후의 경로
    csv_path = Path("csv") / relative_path.parent

    # CSV 저장 폴더 생성
    csv_path.mkdir(parents=True,exist_ok=True)

    # CSV 파일 경로 설정
    csv_file_path = csv_path / data_path.name.replace(".pcap", ".csv")
    if csv_file_path.exists():
        print(f"[INFO] {csv_file_path} already exists.")
        return

    data_path = str(data_path)
    packets = tqdm(rdpcap(data_path))
    
    sessions = OrderedDict()
    initial_ips = {}

    sni = None
    cap = pyshark.FileCapture(str(data_path), display_filter='tls.handshake.extensions_server_name')
    for pkt in cap:
        sh_src_ip = None
        sh_dst_ip = None
        sh_src_port = None
        sh_dst_port = None
        sh_protocol = None
        sni = None
        if hasattr(pkt, 'tls'):
            if hasattr(pkt.tls, 'handshake_extensions_server_name'):
                sh_src_ip = str(pkt.ip.src)
                sh_dst_ip = str(pkt.ip.dst)
                sh_src_port = str(pkt.tcp.srcport)
                sh_dst_port = str(pkt.tcp.dstport)
                sh_protocol = "6"
                sni = pkt.tls.handshake_extensions_server_name
        
                session_key = '_'.join([sh_src_ip, sh_src_port, sh_dst_ip, sh_dst_port, sh_protocol])
        
                sessions[session_key] = {'sni': sni, 'data': []}
                initial_ips[session_key] = (sh_src_ip, sh_dst_ip)
    cap.close()
        
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
        
        if session_key in sessions:
            pass
        elif reversed_key in sessions:
            session_key = reversed_key
        else:
            initial_ips[session_key] = (src_ip, dst_ip)
            sessions[session_key] = {'sni': None, 'data': []}
        
        current_session = sessions[session_key]['data']
        ip1, ip2 = initial_ips[session_key]
        direction = '-' if src_ip == ip1 else  '+'

        packet_size = 0
        if pkt.haslayer("TCP"):
            packet_size = len(bytes(pkt["TCP"].payload))
        elif pkt.haslayer("UDP"):
            packet_size = len(bytes(pkt["UDP"].payload))
        else:
            continue
        
        current_session += [f'{direction}{packet_size}'] if 0 <= packet_size <= 1600 else []

    df_data = []
    
    for key in sessions.keys():
        data = sessions[key]
        splt = data['data']
        key = key.split("_")
        sni = data['sni']
        splt_arr = np.array([int(x) for x in splt])

        df_data.append([
            *key[:4], int_2_prot(int(key[4])), 
            len(splt_arr[splt_arr>0]), 
            len(splt_arr[splt_arr<0]), 
            int(sum(splt_arr[splt_arr>0])), 
            int(sum(splt_arr[splt_arr<0])), 
            len(splt), 
            splt,
            sni
        ])

    df = pd.DataFrame(
        df_data, columns=['Source IP', 'Source Port', 'Destination IP', 'Destination Port', 'Protocol', 'Rx-Pkts','Tx-Pkts', 'Rx-Bytes', 'Tx-Bytes', "SPLT-Len", "SPLT-Data", "SNI"]
    ).sort_values(by=['Rx-Bytes'], axis=0, ascending=False)

    name = os.path.split(data_path)[1]
    print(f'[INFO] df will be saved at ===>', csv_file_path)
            
    df.to_csv(csv_file_path, index=False)

    return df

if __name__ == "__main__":
    pcap_folder = Path("pcap")
    pcap_files = list(pcap_folder.glob("**/*.pcap"))
    for pcap_file in pcap_files:
        print(f"[INFO] Processing {pcap_file}")
        pcap_2_df(pcap_file)