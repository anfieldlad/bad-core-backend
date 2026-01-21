"""Common response schemas."""
from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel


class ExtractionResponse(BaseModel):
    """Response model for extraction endpoints."""
    
    status: Literal["success", "error"]
    source: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    
    message: str
