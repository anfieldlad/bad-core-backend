"""KTP (Indonesian ID Card) document extractor."""
from typing import Dict, Any
from app.services.extractors.base import DocumentExtractor


class KTPExtractor(DocumentExtractor):
    """Extractor for Indonesian KTP (Kartu Tanda Penduduk) documents."""
    
    # Required fields for KTP validation
    REQUIRED_FIELDS = {
        "NIK", "nama", "tempat_lahir", "tanggal_lahir", 
        "jenis_kelamin", "alamat", "agama", "status_perkawinan", 
        "pekerjaan", "kewarganegaraan"
    }
    
    @property
    def document_type(self) -> str:
        """Return document type identifier.
        
        Returns:
            "ktp"
        """
        return "ktp"
    
    @property
    def prompt(self) -> str:
        """Return KTP extraction prompt.
        
        Returns:
            Prompt for extracting KTP data
        """
        return (
            "Extract data from this KTP image to JSON format: "
            "{NIK, nama, tempat_lahir, tanggal_lahir, jenis_kelamin, "
            "alamat, agama, status_perkawinan, pekerjaan, kewarganegaraan}"
        )
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate KTP data has all required fields.
        
        Args:
            data: Extracted KTP data
            
        Returns:
            True if all required fields are present, False otherwise
        """
        if not isinstance(data, dict):
            return False
        
        # Check all required fields are present and non-empty
        for field in self.REQUIRED_FIELDS:
            if field not in data or not data[field]:
                return False
        
        # Validate NIK format (16 digits)
        nik = str(data.get("NIK", ""))
        if not nik.isdigit() or len(nik) != 16:
            return False
        
        return True
    
    def get_unique_identifier(self, data: Dict[str, Any]) -> str:
        """Get NIK as unique identifier for KTP.
        
        Args:
            data: Extracted KTP data
            
        Returns:
            NIK (Nomor Induk Kependudukan)
        """
        return str(data.get("NIK", ""))
