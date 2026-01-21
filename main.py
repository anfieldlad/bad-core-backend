"""Backward compatibility entry point for the application.

This file maintains backward compatibility for existing deployments
that use 'uvicorn main:app'. It imports the new refactored application
from app.main.
"""
from app.main import app

# This allows existing deployments with `uvicorn main:app` to continue working
__all__ = ["app"]
