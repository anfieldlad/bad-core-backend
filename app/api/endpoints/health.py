"""Health check endpoint."""
from fastapi import APIRouter
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check endpoint.
    
    Returns:
        Health status message
    """
    return HealthResponse(message="BAD CORE API is Running!")
