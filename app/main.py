"""FastAPI application initialization."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.core.logging import setup_logging
from app.api.endpoints import health, extraction
from app.db.session import engine
from app.db.base import Base

# Setup logging
setup_logging()

# Initialize database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="BAD CORE API",
    description="Document extraction API with SOLID principles",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(extraction.router, tags=["extraction"])
