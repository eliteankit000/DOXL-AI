#!/usr/bin/env python3
"""
DocXL AI — Universal Document Processing Script
Handles both PDF and Images (JPG/PNG) with automatic routing

Architecture:
- PDF → PyMuPDF extraction
- Image → OCR (PaddleOCR/Tesseract)
- Same table reconstruction pipeline for both
"""
import sys
import os
import json
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from pdf_engine.universal_pipeline import process_document_universal

def main():
    """Entry point for universal document processing."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python extract.py <file_path> [user_requirements]"}))
        sys.exit(1)
    
    file_path = sys.argv[1]
    # user_requirements = sys.argv[2] if len(sys.argv) > 2 else ""  # Not used in algorithmic approach
    
    if not os.path.exists(file_path):
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)
    
    try:
        # Process with universal pipeline (handles PDF and images)
        result = process_document_universal(file_path)
        
        # Output JSON result
        print(json.dumps(result, indent=2))
    
    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "document_type": "unknown",
            "columns": [],
            "rows": [],
            "confidence": 0.0
        }), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
