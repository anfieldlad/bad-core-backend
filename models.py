"""Backward compatibility wrapper for models module.

This file maintains backward compatibility for existing imports.
It re-exports model classes from the new app.models module.
"""
from app.models.document_record import DocumentRecord

# Alias for backward compatibility
KTPRecord = DocumentRecord

# Export for backward compatibility
__all__ = ["KTPRecord", "DocumentRecord"]
