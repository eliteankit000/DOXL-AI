"""
DocXL AI - PDF Engine Package
Production-grade deterministic PDF-to-Excel conversion
NO LLM usage - pure algorithmic approach
"""

__version__ = "9.5.0"
__author__ = "DocXL AI"

# Only export what's actually used
from .universal_pipeline import process_document_universal
from .extractor import extract_words_from_pdf
from .exporter import export_to_excel_buffer

__all__ = [
    'process_document_universal',
    'extract_words_from_pdf',
    'export_to_excel_buffer'
]
