"""Document record model for storing extracted document data."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.db.base import Base


class DocumentRecord(Base):
    """Model for storing document extraction records.
    
    Supports multiple document types (KTP, SIM, Passport, etc.)
    """
    __tablename__ = "ktp_records"  # Keep table name for backward compatibility
    
    id = Column(Integer, primary_key=True, index=True)
    document_type = Column(String, index=True, default="ktp", nullable=False)
    unique_identifier = Column(String, index=True)  # NIK for KTP, nomor_sim for SIM, etc.
    image_hash = Column(String, index=True)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @property
    def nik(self):
        """Backward compatibility property for NIK access.
        
        Returns:
            unique_identifier value (for KTP documents, this is the NIK)
        """
        return self.unique_identifier
    
    @nik.setter
    def nik(self, value):
        """Backward compatibility setter for NIK.
        
        Args:
            value: NIK value to set
        """
        self.unique_identifier = value
