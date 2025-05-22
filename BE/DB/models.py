from DB import db
from sqlalchemy import Enum
import datetime

class PacketLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False)
    src_ip = db.Column(db.String(39), nullable=False) # ex) 192.168.0.205
    src_port = db.Column(db.Integer, nullable=False) # ex) 46702
    dst_ip = db.Column(db.String(39), nullable=False) # ex) 192.168.0.205
    dst_port = db.Column(db.Integer, nullable=False) # ex) 443, 53
    protocol = db.Column(db.SmallInteger, nullable=False) # ex) {"TCP": 6, "UDP": 17, "ICMP": 1}
    size = db.Column(db.Integer, nullable=False) # 38 (단위 : Byte)
    direction = db.Column(Enum('UPLOAD', 'DOWNLOAD', name='direction_enum'), nullable=False) # ex) UPLOAD, DOWNLOAD

    def __repr__(self):
        return f'<PacketLog {self.timestamp} {self.src_ip}:{self.src_port} -> {self.dst_ip}:{self.dst_port}>'