#!/bin/bash

SCRIPT_DIR="/home/jang/Documents/new_pcap/capstone-2025-35/auto_flow" #자동화 파일 위치
TO_DF_FILE="/home/jang/Documents/new_pcap/capstone-2025-35/to_df.py" #to_df 경로
PCAP_DIR="/home/jang/Documents/new_pcap/capstone-2025-35/pcap"  # 실제 save_dir 경로로 수정하세요

# 1. 실행 전 기존 pcap 파일 목록 저장
existing_files=$(find "$PCAP_DIR" -type f -name '*.pcap')

# 2. to_df.py를 제외한 모든 .py 파일 실행
for file in "$SCRIPT_DIR"/*.py
do
    if [[ "$file" == "$TO_DF_FILE" ]]; then
        continue
    fi

    echo "Running $file..."
    python "$file"
done

# 3. to_df.py 실행
echo "Running $TO_DF_FILE..."
python "$TO_DF_FILE"

# 4. 실행 후 전체 pcap 파일 목록에서 기존 파일을 제외하고 삭제
echo "Deleting only newly created .pcap files..."
current_files=$(find "$PCAP_DIR" -type f -name '*.pcap')

for f in $current_files; do
    if ! echo "$existing_files" | grep -qx "$f"; then
        echo "Deleting: $f"
        rm "$f"
    fi
done

echo "Done."
