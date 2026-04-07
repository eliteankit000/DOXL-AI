"""
DocXL AI - Document Segmentation Engine
Detects and classifies blocks (tables vs metadata)
"""
from typing import List, Dict
from collections import defaultdict

# Keywords for table detection
TABLE_KEYWORDS = {
    'main_table': ['particular', 'description', 'item', 'amount', 'price', 'qty', 'quantity', 'rate', 'total'],
    'tax_table': ['tax', 'cgst', 'sgst', 'igst', 'gst', 'vat'],
    'metadata': ['guest', 'bill', 'invoice', 'date', 'no', 'number', 'name', 'address']
}

def group_words_into_blocks(words: List[Dict], vertical_gap_threshold: float = 15.0) -> List[List[Dict]]:
    """
    Group words into blocks using vertical gap detection.
    
    Args:
        words: List of word dictionaries
        vertical_gap_threshold: Minimum Y-distance to consider a new block
        
    Returns:
        List of blocks (each block is a list of words)
    """
    if not words:
        return []
    
    # Sort by page and Y position
    sorted_words = sorted(words, key=lambda w: (w['page'], w['y0']))
    
    blocks = []
    current_block = [sorted_words[0]]
    last_y1 = sorted_words[0]['y1']
    last_page = sorted_words[0]['page']
    
    for word in sorted_words[1:]:
        # New page = new block
        if word['page'] != last_page:
            blocks.append(current_block)
            current_block = [word]
            last_y1 = word['y1']
            last_page = word['page']
            continue
        
        # Check vertical gap
        gap = word['y0'] - last_y1
        
        if gap > vertical_gap_threshold:
            # New block
            blocks.append(current_block)
            current_block = [word]
        else:
            # Same block
            current_block.append(word)
        
        last_y1 = max(last_y1, word['y1'])
    
    # Add last block
    if current_block:
        blocks.append(current_block)
    
    return blocks


def classify_block(block: List[Dict]) -> str:
    """
    Classify block type using keyword matching.
    
    Returns:
        'main_table', 'tax_table', 'metadata', or 'ignore'
    """
    if not block:
        return 'ignore'
    
    # Extract all text from block
    block_text = ' '.join([w['text'].lower() for w in block])
    
    # Check for table keywords
    main_table_score = sum(1 for kw in TABLE_KEYWORDS['main_table'] if kw in block_text)
    tax_table_score = sum(1 for kw in TABLE_KEYWORDS['tax_table'] if kw in block_text)
    metadata_score = sum(1 for kw in TABLE_KEYWORDS['metadata'] if kw in block_text)
    
    # Classification logic
    if main_table_score >= 2:
        return 'main_table'
    elif tax_table_score >= 1:
        return 'tax_table'
    elif metadata_score >= 1:
        return 'metadata'
    else:
        return 'ignore'


def segment_document(words: List[Dict]) -> Dict[str, List[List[Dict]]]:
    """
    Segment document into classified blocks.
    
    Returns:
        Dictionary with keys: 'main_table', 'tax_table', 'metadata', 'ignore'
    """
    blocks = group_words_into_blocks(words)
    
    segmented = defaultdict(list)
    
    for block in blocks:
        block_type = classify_block(block)
        segmented[block_type].append(block)
    
    return dict(segmented)
