"""Base document extractor following Open/Closed Principle."""
from abc import ABC, abstractmethod
from typing import Dict, Any


class DocumentExtractor(ABC):
    """Abstract base class for document extractors.
    
    New document types can be added by extending this class without
    modifying existing code (Open/Closed Principle).
    """
    
    @property
    @abstractmethod
    def document_type(self) -> str:
        """Return the document type identifier.
        
        Returns:
            Document type (e.g., "ktp", "sim", "passport")
        """
        pass
    
    @property
    @abstractmethod
    def prompt(self) -> str:
        """Return the extraction prompt for this document type.
        
        Returns:
            OCR prompt specific to this document type
        """
        pass
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate extracted data meets requirements.
        
        Args:
            data: Extracted data dictionary
            
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_unique_identifier(self, data: Dict[str, Any]) -> str:
        """Return the unique identifier from extracted data.
        
        Args:
            data: Extracted data dictionary
            
        Returns:
            Unique identifier (e.g., NIK for KTP)
        """
        pass
