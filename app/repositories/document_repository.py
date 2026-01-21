"""Repository for document record database operations."""
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.document_record import DocumentRecord
from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentRepository:
    """Repository for managing document records in the database."""
    
    def __init__(self, db: Session):
        """Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self._db = db
    
    def find_by_hash(self, image_hash: str) -> Optional[DocumentRecord]:
        """Find document record by image hash.
        
        Args:
            image_hash: SHA256 hash of the image
            
        Returns:
            Document record if found, None otherwise
        """
        return self._db.query(DocumentRecord).filter(
            DocumentRecord.image_hash == image_hash
        ).first()
    
    def find_by_identifier(
        self, 
        identifier: str, 
        document_type: str,
        max_age_days: int = 30
    ) -> Optional[DocumentRecord]:
        """Find recent document record by unique identifier.
        
        Args:
            identifier: Unique identifier (e.g., NIK for KTP)
            document_type: Type of document (e.g., "ktp")
            max_age_days: Maximum age in days for cache validity
            
        Returns:
            Document record if found and within age limit, None otherwise
        """
        cutoff = datetime.utcnow() - timedelta(days=max_age_days)
        return self._db.query(DocumentRecord).filter(
            DocumentRecord.unique_identifier == identifier,
            DocumentRecord.document_type == document_type,
            DocumentRecord.created_at >= cutoff
        ).first()
    
    def create(self, record: DocumentRecord) -> DocumentRecord:
        """Create new document record.
        
        Args:
            record: Document record to create
            
        Returns:
            Created document record with ID
        """
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        logger.info(f"Created document record: type={record.document_type}, id={record.id}")
        return record
    
    def update_hash(self, record: DocumentRecord, new_hash: str) -> None:
        """Update image hash for existing record.
        
        Args:
            record: Document record to update
            new_hash: New image hash value
        """
        record.image_hash = new_hash
        self._db.commit()
        logger.info(f"Updated hash for record id={record.id}")
