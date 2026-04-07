"""
DocXL AI - Main Pipeline Orchestrator
Production-grade PDF-to-Excel conversion (NO LLM)
"""
import time
from typing import Dict
from pathlib import Path

from .extractor import extract_words_from_pdf
from .segmentation import segment_document
from .table_engine import reconstruct_table
from .validation import validate_and_clean_table
from .exporter import convert_to_output_format

def process_pdf_to_excel(pdf_path: str) -> Dict:
    """
    Main pipeline: PDF → Words → Blocks → Tables → Validation → Output
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        {
            'columns': List[str],
            'rows': List[Dict],
            'document_type': str,
            'confidence': float,
            'processing_time': float
        }
    """
    start_time = time.time()
    
    print(f"[PIPELINE] Starting PDF processing: {pdf_path}")
    
    # LAYER 1: Extract words with bounding boxes
    print("[LAYER 1] Extracting words...")
    words = extract_words_from_pdf(pdf_path, page_limit=10)
    print(f"[LAYER 1] Extracted {len(words)} words")
    
    if not words:
        return {
            'columns': [],
            'rows': [],
            'document_type': 'unknown',
            'confidence': 0.0,
            'processing_time': time.time() - start_time,
            'error': 'No text extracted from PDF'
        }
    
    # LAYER 2: Segment into blocks
    print("[LAYER 2] Segmenting document...")
    segmented = segment_document(words)
    print(f"[LAYER 2] Found blocks: {', '.join([f'{k}={len(v)}' for k, v in segmented.items()])}")
    
    # Process main table (priority)
    table_data = None
    
    if 'main_table' in segmented and segmented['main_table']:
        print("[LAYER 3] Reconstructing main table...")
        table_block = segmented['main_table'][0]  # Take first main table
        table_data = reconstruct_table(table_block)
    
    elif 'tax_table' in segmented and segmented['tax_table']:
        print("[LAYER 3] Reconstructing tax table...")
        table_block = segmented['tax_table'][0]
        table_data = reconstruct_table(table_block)
    
    else:
        # Fallback: try all words as one block
        print("[LAYER 3] No table detected, processing all words...")
        table_data = reconstruct_table(words)
    
    if not table_data or not table_data.get('rows'):
        return {
            'columns': [],
            'rows': [],
            'document_type': 'unknown',
            'confidence': 0.0,
            'processing_time': time.time() - start_time,
            'error': 'No table structure detected'
        }
    
    print(f"[LAYER 3] Reconstructed {len(table_data['rows'])} rows, {table_data['column_count']} columns")
    
    # LAYER 4: Validate and clean
    print("[LAYER 4] Validating and cleaning...")
    table_data = validate_and_clean_table(table_data)
    print(f"[LAYER 4] After cleaning: {len(table_data['rows'])} rows")
    
    # LAYER 5: Convert to output format
    print("[LAYER 5] Converting to output format...")
    output = convert_to_output_format(table_data)
    output['processing_time'] = time.time() - start_time
    
    print(f"[PIPELINE] Complete in {output['processing_time']:.2f}s")
    print(f"[PIPELINE] Output: {len(output['rows'])} rows, {len(output['columns'])} columns")
    
    return output
