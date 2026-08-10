import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ktp.db")

# If it's a supabase/postgres URL, we might need to handle the 'postgres://' vs 'postgresql://' protocol
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Diagnostic: Print the host being used
try:
    host_name = DATABASE_URL.split("@")[1].split(":")[0]
    print(f"INFO: Connecting to database host: {host_name}")
except Exception:
    print(f"INFO: Connecting to database: {DATABASE_URL}")

# pool_pre_ping validates a pooled connection before handing it out. Without it,
# connections held across a database outage (e.g. a paused Supabase project) are
# stale on return and the first request after recovery fails.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
