"""
DocXL AI — PDF Engine Package
pdfplumber + openpyxl based PDF-to-Excel conversion
"""

__version__ = "11.0.0"
__author__ = "DocXL AI"

from .extractor import extract_and_build, get_extraction_summary

__all__ = [
    'extract_and_build',
    'get_extraction_summary',
]
