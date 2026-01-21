"""Gemini OCR provider implementation."""
import google.genai as genai
from app.services.interfaces.ocr_provider import OCRProvider
from app.config.settings import Settings
from app.core.exceptions import DocumentExtractionError
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiProvider(OCRProvider):
    """Google Gemini implementation of OCR provider."""
    
    def __init__(self, settings: Settings):
        """Initialize Gemini provider.
        
        Args:
            settings: Application settings containing API key
        """
        self._client = genai.Client(api_key=settings.google_api_key)
        self._model = settings.gemini_model
    
    def extract_text(self, image_data: bytes, mime_type: str, prompt: str) -> str:
        """Extract text from image using Gemini API.
        
        Args:
            image_data: Raw image bytes
            mime_type: MIME type of the image
            prompt: Extraction prompt
            
        Returns:
            Extracted text from Gemini
            
        Raises:
            DocumentExtractionError: If Gemini API call fails
        """
        try:
            logger.info(f"Calling Gemini API with model: {self._model}")
            response = self._client.models.generate_content(
                model=self._model,
                contents=[
                    genai.types.Part.from_bytes(data=image_data, mime_type=mime_type),
                    prompt
                ]
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise DocumentExtractionError(f"Failed to extract document data: {str(e)}")
