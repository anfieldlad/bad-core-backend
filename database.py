"""Backward compatibility wrapper for database module.

This file maintains backward compatibility for existing imports.
It re-exports database objects from the new app.db.session module.
"""
from app.db.session import SessionLocal, engine, get_db
from app.db.base import Base

# Export for backward compatibility
__all__ = ["SessionLocal", "engine", "get_db", "Base"]
