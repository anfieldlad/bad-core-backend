"""Document extraction endpoint."""
from fastapi import APIRouter, UploadFile, File, Depends
from app.services.extraction_service import ExtractionService
from app.api.deps import get_extraction_service
from app.core.security import verify_api_key
from app.schemas.common import ExtractionResponse
from app.core.exceptions import InvalidDocumentError, DocumentExtractionError
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/extract", response_model=ExtractionResponse)
async def extract_document(
    file: UploadFile = File(...),
    service: ExtractionService = Depends(get_extraction_service),
    api_key: str = Depends(verify_api_key)
) -> ExtractionResponse:
    """Extract data from KTP document image.
    
    Args:
        file: Uploaded image file
        service: Extraction service dependency
        api_key: Validated API key
        
    Returns:
        Extraction response with status, source, and data
    """
    try:
        # Read file content
        content = await file.read()
        
        # Extract document (default to KTP for backward compatibility)
        result = await service.extract(
            document_type="ktp",
            image_data=content,
            mime_type=file.content_type or "image/jpeg"
        )
        
        return ExtractionResponse(
            status=result["status"],
            source=result["source"],
            data=result["data"]
        )
        
    except (InvalidDocumentError, DocumentExtractionError) as e:
        logger.error(f"Extraction error: {str(e)}")
        return ExtractionResponse(
            status="error",
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return ExtractionResponse(
            status="error",
            detail=str(e)
        )
