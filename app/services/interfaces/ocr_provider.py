"""Abstract OCR provider interface following Dependency Inversion Principle."""
from abc import ABC, abstractmethod


class OCRProvider(ABC):
    """Interface for OCR providers.
    
    This abstraction allows easy swapping of OCR providers without
    changing business logic.
    """
    
    @abstractmethod
    def extract_text(self, image_data: bytes, mime_type: str, prompt: str) -> str:
        """Extract text from image using the given prompt.
        
        Args:
            image_data: Raw image bytes
            mime_type: MIME type of the image (e.g., "image/jpeg")
            prompt: Extraction prompt to guide the OCR
            
        Returns:
            Extracted text/JSON from the image
            
        Raises:
            DocumentExtractionError: If extraction fails
        """
        pass
