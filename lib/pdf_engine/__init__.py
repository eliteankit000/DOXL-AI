"""
DocXL AI — PDF Engine Package
pdfplumber-based PDF-to-Excel conversion
"""

__version__ = "10.0.0"
__author__ = "DocXL AI"

from .pipeline import process
from .excel_builder import build_excel

__all__ = [
    'process',
    'build_excel',
]
