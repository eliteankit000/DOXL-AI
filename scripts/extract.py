#!/usr/bin/env python3
"""
DocXL AI — Production PDF-to-Excel Engine
DETERMINISTIC ALGORITHMIC APPROACH (NO LLM)

Uses PyMuPDF for fast word extraction with coordinates.
Implements table reconstruction using row/column clustering.
Target: <1-2 seconds per page.
"""
import sys
import os
import json
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from pdf_engine import process_pdf_to_excel

def main():
    """Entry point for PDF processing script."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python extract.py <file_path> [user_requirements]"}))
        sys.exit(1)
    
    file_path = sys.argv[1]
    # user_requirements = sys.argv[2] if len(sys.argv) > 2 else ""  # Not used in algorithmic approach
    
    if not os.path.exists(file_path):
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)
    
    file_ext = Path(file_path).suffix.lower()
    
    # Only process PDFs with PyMuPDF engine
    if file_ext != '.pdf':
        print(json.dumps({
            "error": "Only PDF files supported by PyMuPDF engine. Use image extraction for images.",
            "document_type": "unknown",
            "columns": [],
            "rows": [],
            "confidence": 0.0
        }))
        sys.exit(1)
    
    try:
        # Process PDF with deterministic algorithm
        result = process_pdf_to_excel(file_path)
        
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
