"""Database session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Handle postgres:// vs postgresql:// protocol
database_url = settings.database_url
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Log connection info
try:
    host_name = database_url.split("@")[1].split(":")[0] if "@" in database_url else "local"
    logger.info(f"Connecting to database host: {host_name}")
except Exception:
    logger.info(f"Connecting to database: {database_url}")

engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session dependency.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
