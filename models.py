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


class Keepalive(Base):
    """Single-row table written on a schedule to keep the Supabase project active.

    Supabase pauses Free plan projects after ~7 days of low database activity. A
    periodic write resets that timer. Deliberately one row (id is always 1) so the
    table never grows; see keepalive.py.
    """

    __tablename__ = "keepalive"

    id = Column(Integer, primary_key=True)
    last_ping = Column(DateTime(timezone=True), nullable=False)
