"""Custom exception classes for the application."""
from typing import Any, Dict


class AppException(Exception):
    """Base application exception."""
    pass


class DocumentExtractionError(AppException):
    """Raised when document extraction fails."""
    pass


class InvalidDocumentError(AppException):
    """Raised when document validation fails."""
    pass


class CacheHitException(AppException):
    """Raised to signal a cache hit - used for flow control."""
    
    def __init__(self, data: Dict[str, Any], source: str):
        """Initialize cache hit exception.
        
        Args:
            data: The cached data
            source: The cache source (e.g., "cache (hash matching)")
        """
        self.data = data
        self.source = source
        super().__init__(f"Cache hit from {source}")
