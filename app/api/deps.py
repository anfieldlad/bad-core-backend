"""Shared API dependencies."""
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.config.settings import settings
from app.services.extraction_service import ExtractionService
from app.services.ocr.gemini_provider import GeminiProvider
from app.services.extractors.ktp_extractor import KTPExtractor
from app.repositories.document_repository import DocumentRepository


def get_extraction_service(db: Session = Depends(get_db)) -> ExtractionService:
    """Get extraction service dependency.
    
    This function provides dependency injection for the extraction service,
    wiring together all dependencies.
    
    Args:
        db: Database session
        
    Returns:
        Configured extraction service
    """
    
    # Create OCR provider
    ocr_provider = GeminiProvider(settings)
    
    # Create repository
    repository = DocumentRepository(db)
    
    # Register extractors
    extractors = {
        "ktp": KTPExtractor()
    }
    
    return ExtractionService(
        ocr_provider=ocr_provider,
        repository=repository,
        extractors=extractors
    )
