#!/usr/bin/env python3
"""
DocXL AI - PyMuPDF Table Extraction (NO LLM)
Deterministic algorithmic approach - Nitro PDF quality
"""
import sys
import os
import json
import time
from pathlib import Path

def extract_with_pymupdf(file_path: str) -> dict:
    """
    Production PyMuPDF extraction with table reconstruction.
    Uses deterministic algorithm - NO LLM calls.
    """
    try:
        import fitz  # PyMuPDF
        
        start_time = time.time()
        
        print(f"[DEBUG] Starting extraction: {file_path}", file=sys.stderr)
        
        # Try to use modular pipeline if available
        try:
            # Import the modular pipeline
            sys.path.insert(0, '/app')
            from lib.pdf_engine.universal_pipeline import process_document_universal
            
            print("[DEBUG] Using modular PyMuPDF pipeline", file=sys.stderr)
            result = process_document_universal(file_path)
            
            # Add debug info
            columns = result.get('columns', [])
            rows = result.get('rows', [])
            
            print(f"[DEBUG] Extraction complete", file=sys.stderr)
            print(f"[DEBUG] Columns: {len(columns)}", file=sys.stderr)
            print(f"[DEBUG] Rows: {len(rows)}", file=sys.stderr)
            
            # Check if empty - RETRY with relaxed settings
            if len(rows) == 0 or len(columns) < 2:
                print("[DEBUG] Empty result - retrying with relaxed rules", file=sys.stderr)
                # Try fallback extraction
                result = simple_fallback_extract(file_path)
                
                columns = result.get('columns', [])
                rows = result.get('rows', [])
                print(f"[DEBUG] Fallback - Columns: {len(columns)}, Rows: {len(rows)}", file=sys.stderr)
            
            # Add processing time
            result['processing_time'] = time.time() - start_time
            
            return result
            
        except Exception as pipeline_error:
            print(f"[DEBUG] Pipeline error: {str(pipeline_error)}", file=sys.stderr)
            print("[DEBUG] Falling back to simple extraction", file=sys.stderr)
            return simple_fallback_extract(file_path)
            
    except Exception as e:
        print(f"[DEBUG] Fatal error: {str(e)}", file=sys.stderr)
        return {
            'columns': [],
            'rows': [],
            'document_type': 'unknown',
            'confidence': 0.0,
            'error': f'Extraction failed: {str(e)}'
        }


def simple_fallback_extract(file_path: str) -> dict:
    """
    Fallback extraction when modular pipeline fails.
    Simple text-based extraction.
    """
    try:
        import fitz  # PyMuPDF
        
        print("[DEBUG] Running fallback extraction", file=sys.stderr)
        
        # Open document
        doc = fitz.open(file_path)
        
        # Extract all text
        all_text = []
        for page_num, page in enumerate(doc[:10]):  # Max 10 pages
            text = page.get_text()
            all_text.append(text)
            print(f"[DEBUG] Page {page_num + 1}: {len(text)} chars", file=sys.stderr)
        
        doc.close()
        
        # Split into lines
        combined_text = '\n'.join(all_text)
        lines = [line.strip() for line in combined_text.split('\n') if line.strip()]
        
        print(f"[DEBUG] Total lines extracted: {len(lines)}", file=sys.stderr)
        
        # Create simple table
        if len(lines) > 0:
            headers = ['Content']
            rows = [{'Content': line} for line in lines[:100]]  # Max 100 rows
            
            print(f"[DEBUG] Fallback result - 1 column, {len(rows)} rows", file=sys.stderr)
            
            return {
                'columns': headers,
                'rows': rows,
                'document_type': 'text',
                'confidence': 0.70,
                'extraction_method': 'fallback_text'
            }
        else:
            print("[DEBUG] No text found in document", file=sys.stderr)
            return {
                'columns': [],
                'rows': [],
                'document_type': 'unknown',
                'confidence': 0.0,
                'error': 'No structured table detected'
            }
            
    except Exception as e:
        print(f"[DEBUG] Fallback error: {str(e)}", file=sys.stderr)
        return {
            'columns': [],
            'rows': [],
            'document_type': 'unknown',
            'confidence': 0.0,
            'error': f'Fallback extraction failed: {str(e)}'
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
    
    print(f"[DEBUG] File: {file_path}", file=sys.stderr)
    print(f"[DEBUG] File size: {os.path.getsize(file_path)} bytes", file=sys.stderr)
    
    result = extract_with_pymupdf(file_path)
    
    # Output result as JSON to stdout
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
