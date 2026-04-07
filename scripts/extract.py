#!/usr/bin/env python3
"""
DocXL AI - Simple Direct Extraction (NO COMPLEXITY)
Fast PDF-to-JSON conversion
"""
import sys
import os
import json
from pathlib import Path

def simple_extract(file_path: str) -> dict:
    """Simple fast extraction."""
    try:
        import fitz  # PyMuPDF
        import time
        
        start_time = time.time()
        
        # Open PDF
        doc = fitz.open(file_path)
        
        # Get all text
        all_text = []
        for page in doc[:10]:  # Max 10 pages
            text = page.get_text()
            all_text.append(text)
        
        doc.close()
        
        # Simple split into rows
        combined_text = '\n'.join(all_text)
        lines = [line.strip() for line in combined_text.split('\n') if line.strip()]
        
        # Create simple table
        if len(lines) > 0:
            # First line as header
            headers = ['Content']
            rows = [{'Content': line} for line in lines[:100]]  # Max 100 rows
            
            return {
                'columns': headers,
                'rows': rows,
                'document_type': 'text',
                'confidence': 0.90,
                'processing_time': time.time() - start_time,
                'extraction_method': 'simple_text'
            }
        else:
            return {
                'columns': [],
                'rows': [],
                'document_type': 'unknown',
                'confidence': 0.0,
                'processing_time': time.time() - start_time,
                'error': 'No text found'
            }
            
    except Exception as e:
        return {
            'columns': [],
            'rows': [],
            'document_type': 'unknown',
            'confidence': 0.0,
            'error': str(e)
        }

def main():
    """Entry point."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python extract.py <file_path>"}))
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)
    
    result = simple_extract(file_path)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
