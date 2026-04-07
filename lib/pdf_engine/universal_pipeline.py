"""
DocXL AI - Universal Pipeline
Routes to PDF or Image processing based on file type
"""
import time
from typing import Dict
from pathlib import Path

from .extractor import extract_words_from_pdf
from .image_engine import process_image
from .segmentation import segment_document
from .table_engine import reconstruct_table
from .validation import validate_and_clean_table
from .exporter import convert_to_output_format

def detect_file_type(file_path: str) -> str:
    """
    Detect file type from extension.
    
    Returns:
        'pdf', 'image', or 'unknown'
    """
    ext = Path(file_path).suffix.lower()
    
    if ext == '.pdf':
        return 'pdf'
    elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        return 'image'
    else:
        return 'unknown'


def process_document_universal(file_path: str) -> Dict:
    """
    Universal pipeline that handles both PDF and images.
    
    Architecture:
    - Detects file type
    - Routes to appropriate extraction method
    - Uses SAME table reconstruction pipeline
    
    Returns:
        {
            'columns': List[str],
            'rows': List[Dict],
            'document_type': str,
            'confidence': float,
            'processing_time': float,
            'extraction_method': str
        }
    """
    start_time = time.time()
    
    print(f"[UNIVERSAL_PIPELINE] Processing: {file_path}")
    
    # Detect file type
    file_type = detect_file_type(file_path)
    print(f"[UNIVERSAL_PIPELINE] Detected file type: {file_type}")
    
    # ROUTE 1: Extract words based on file type
    if file_type == 'pdf':
        print("[ROUTE] Using PyMuPDF extraction...")
        words = extract_words_from_pdf(file_path, page_limit=10)
        extraction_method = 'pymupdf_algorithmic'
    
    elif file_type == 'image':
        print("[ROUTE] Using OCR extraction...")
        words = process_image(file_path)
        extraction_method = 'ocr_paddleocr'
    
    else:
        return {
            'columns': [],
            'rows': [],
            'document_type': 'unknown',
            'confidence': 0.0,
            'processing_time': time.time() - start_time,
            'error': f'Unsupported file type: {file_type}'
        }
    
    if not words:
        return {
            'columns': [],
            'rows': [],
            'document_type': 'unknown',
            'confidence': 0.0,
            'processing_time': time.time() - start_time,
            'error': 'No text extracted from file',
            'extraction_method': extraction_method
        }
    
    print(f"[UNIVERSAL_PIPELINE] Extracted {len(words)} words")
    
    # ROUTE 2: SAME PIPELINE FOR BOTH
    # Segment into blocks
    segmented = segment_document(words)
    print(f"[UNIVERSAL_PIPELINE] Segmented: {', '.join([f'{k}={len(v)}' for k, v in segmented.items()])}")
    
    # Reconstruct table
    table_data = None
    
    if 'main_table' in segmented and segmented['main_table']:
        table_block = segmented['main_table'][0]
        table_data = reconstruct_table(table_block)
    elif 'tax_table' in segmented and segmented['tax_table']:
        table_block = segmented['tax_table'][0]
        table_data = reconstruct_table(table_block)
    else:
        # Fallback: process all words
        table_data = reconstruct_table(words)
    
    if not table_data or not table_data.get('rows'):
        return {
            'columns': [],
            'rows': [],
            'document_type': 'unknown',
            'confidence': 0.0,
            'processing_time': time.time() - start_time,
            'error': 'No table structure detected',
            'extraction_method': extraction_method
        }
    
    print(f"[UNIVERSAL_PIPELINE] Reconstructed {len(table_data['rows'])} rows")
    
    # Validate and clean
    table_data = validate_and_clean_table(table_data)
    
    # Convert to output format
    output = convert_to_output_format(table_data)
    output['processing_time'] = time.time() - start_time
    output['extraction_method'] = extraction_method
    
    print(f"[UNIVERSAL_PIPELINE] Complete in {output['processing_time']:.2f}s")
    
    return output
