from DB import db
from DB.models import PacketLog
from datetime import datetime

def insert_packet_log(timestamp, src_ip, src_port, dst_ip, dst_port, protocol, size, direction):
    try:
        new_log = PacketLog(
            timestamp=timestamp if isinstance(timestamp, datetime) else datetime.fromtimestamp(timestamp / 1000),
            src_ip=src_ip,
            src_port=src_port,
            dst_ip=dst_ip,
            dst_port=dst_port,
            protocol=protocol,
            size=size,
            direction=direction
        )
        db.session.add(new_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] DB 삽입 실패: {e}")