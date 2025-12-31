from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from database import Base

class KTPRecord(Base):
    __tablename__ = "ktp_records"

    id = Column(Integer, primary_key=True, index=True)
    nik = Column(String, index=True)
    image_hash = Column(String, index=True)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
