"""
DocXL AI - PDF Engine Package
Production-grade deterministic PDF-to-Excel conversion
NO LLM usage - pure algorithmic approach
"""

__version__ = "1.0.0"
__author__ = "DocXL AI"

from .pipeline import process_pdf_to_excel
from .extractor import extract_words_from_pdf
from .exporter import export_to_excel_buffer

__all__ = [
    'process_pdf_to_excel',
    'extract_words_from_pdf',
    'export_to_excel_buffer'
]
