"""Main extraction service orchestrating document extraction workflow."""
import hashlib
import json
from typing import Dict, Any
from app.services.interfaces.ocr_provider import OCRProvider
from app.services.extractors.base import DocumentExtractor
from app.repositories.document_repository import DocumentRepository
from app.models.document_record import DocumentRecord
from app.core.exceptions import InvalidDocumentError, DocumentExtractionError
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExtractionService:
    """Service for orchestrating document extraction workflow.
    
    This service follows the Dependency Inversion Principle by depending
    on abstractions (OCRProvider, DocumentExtractor) rather than concrete
    implementations.
    """
    
    def __init__(
        self,
        ocr_provider: OCRProvider,
        repository: DocumentRepository,
        extractors: Dict[str, DocumentExtractor]
    ):
        """Initialize extraction service.
        
        Args:
            ocr_provider: OCR provider implementation
            repository: Document repository for database operations
            extractors: Dictionary of extractors by document type
        """
        self._ocr = ocr_provider
        self._repository = repository
        self._extractors = extractors
    
    async def extract(
        self, 
        document_type: str,
        image_data: bytes, 
        mime_type: str
    ) -> Dict[str, Any]:
        """Extract data from document image.
        
        Args:
            document_type: Type of document (e.g., "ktp")
            image_data: Raw image bytes
            mime_type: MIME type of the image
            
        Returns:
            Dictionary with status, source, and extracted data
            
        Raises:
            ValueError: If document type is not supported
            InvalidDocumentError: If extracted data validation fails
            DocumentExtractionError: If OCR extraction fails
        """
        # Get extractor for document type
        extractor = self._extractors.get(document_type)
        if not extractor:
            raise ValueError(f"Unsupported document type: {document_type}")
        
        logger.info(f"Starting extraction for document type: {document_type}")
        
        # Check cache by hash
        image_hash = hashlib.sha256(image_data).hexdigest()
        cached = self._repository.find_by_hash(image_hash)
        if cached:
            logger.info(f"Cache hit by hash for document id={cached.id}")
            return {
                "status": "success", 
                "source": "cache (hash matching)", 
                "data": cached.data
            }
        
        # Extract via OCR
        logger.info("No hash match, calling OCR provider")
        raw_text = self._ocr.extract_text(image_data, mime_type, extractor.prompt)
        data = self._parse_json(raw_text)
        
        # Validate extracted data
        if not extractor.validate(data):
            logger.error(f"Validation failed for extracted data: {data}")
            raise InvalidDocumentError("Extracted data validation failed")
        
        logger.info("Data extraction and validation successful")
        
        # Check cache by unique identifier
        unique_id = extractor.get_unique_identifier(data)
        existing = self._repository.find_by_identifier(unique_id, document_type)
        if existing:
            logger.info(f"Cache hit by identifier for document id={existing.id}")
            # Update hash for future quick lookups
            self._repository.update_hash(existing, image_hash)
            return {
                "status": "success", 
                "source": "cache (identifier matching)", 
                "data": existing.data
            }
        
        # Save new record
        logger.info("Creating new document record")
        self._repository.create(DocumentRecord(
            document_type=document_type,
            unique_identifier=unique_id,
            image_hash=image_hash,
            data=data
        ))
        
        return {"status": "success", "source": "gemini", "data": data}
    
    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Parse JSON from OCR response.
        
        Args:
            text: Raw text response that may contain JSON
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            DocumentExtractionError: If JSON parsing fails
        """
        try:
            # Clean markdown code blocks if present
            clean = text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise DocumentExtractionError(f"Failed to parse extracted data as JSON: {str(e)}")
