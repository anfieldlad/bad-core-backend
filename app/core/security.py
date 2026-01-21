"""Security and authentication logic."""
from fastapi import Header, HTTPException, status
from app.config.settings import settings


def verify_api_key(x_api_key: str = Header(..., description="API Key for authentication")) -> str:
    """Verify the API key from request headers.
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        The validated API key
        
    Raises:
        HTTPException: If API key is invalid or not configured
    """
    if not settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_KEY not configured on server"
        )
    
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    
    return x_api_key
