"""
DocXL AI - Table Reconstruction Engine (CORE)
Algorithmic table reconstruction with perfect row/column alignment
"""
from typing import List, Dict, Tuple
import re

# Header keywords for column detection
HEADER_KEYWORDS = [
    'particular', 'description', 'item', 'product', 'service',
    'amount', 'price', 'rate', 'cost', 'value',
    'qty', 'quantity', 'qnty',
    'total', 'sum', 'subtotal',
    'tax', 'cgst', 'sgst', 'igst', 'gst',
    'date', 'no', 'number', '#'
]

def cluster_words_into_rows(words: List[Dict], y_threshold: float = 5.0) -> List[List[Dict]]:
    """
    Cluster words into rows using Y-axis proximity.
    
    Args:
        words: List of words in a block
        y_threshold: Maximum Y-distance to consider same row
        
    Returns:
        List of rows (each row is list of words sorted left-to-right)
    """
    if not words:
        return []
    
    # Sort by Y position
    sorted_words = sorted(words, key=lambda w: w['y0'])
    
    rows = []
    current_row = [sorted_words[0]]
    current_y = sorted_words[0]['y0']
    
    for word in sorted_words[1:]:
        if abs(word['y0'] - current_y) <= y_threshold:
            # Same row
            current_row.append(word)
        else:
            # New row - sort current row left-to-right
            current_row.sort(key=lambda w: w['x0'])
            rows.append(current_row)
            current_row = [word]
            current_y = word['y0']
    
    # Add last row
    if current_row:
        current_row.sort(key=lambda w: w['x0'])
        rows.append(current_row)
    
    return rows


def detect_header_row(rows: List[List[Dict]]) -> Tuple[int, List[str]]:
    """
    Detect header row using keyword matching.
    
    Returns:
        (header_row_index, header_labels)
    """
    best_score = 0
    best_idx = 0
    best_headers = []
    
    for idx, row in enumerate(rows[:5]):  # Check first 5 rows only
        row_text = ' '.join([w['text'].lower() for w in row])
        score = sum(1 for kw in HEADER_KEYWORDS if kw in row_text)
        
        if score > best_score:
            best_score = score
            best_idx = idx
            best_headers = [w['text'] for w in row]
    
    return (best_idx, best_headers)


def build_column_boundaries(header_row: List[Dict], buffer: float = 10.0) -> List[Tuple[float, float]]:
    """
    Build column boundaries from header row positions.
    
    Args:
        header_row: List of words in header row
        buffer: Extra space to add to last column
        
    Returns:
        List of (x_start, x_end) tuples for each column
    """
    if not header_row:
        return []
    
    # Extract x0 positions
    x_positions = sorted([w['x0'] for w in header_row])
    
    # Build ranges
    boundaries = []
    for i in range(len(x_positions)):
        x_start = x_positions[i]
        x_end = x_positions[i + 1] if i + 1 < len(x_positions) else x_positions[i] + 1000  # Large buffer for last column
        boundaries.append((x_start, x_end))
    
    return boundaries


def assign_words_to_columns(row_words: List[Dict], column_boundaries: List[Tuple[float, float]]) -> List[str]:
    """
    Assign words to columns based on X position.
    
    Returns:
        List of cell values (one per column)
    """
    cells = [''] * len(column_boundaries)
    
    for word in row_words:
        word_x = word['x0']
        
        # Find matching column
        for col_idx, (x_start, x_end) in enumerate(column_boundaries):
            if x_start <= word_x < x_end:
                if cells[col_idx]:
                    cells[col_idx] += ' ' + word['text']
                else:
                    cells[col_idx] = word['text']
                break
    
    return cells


def merge_multiline_cells(rows_data: List[List[str]]) -> List[List[str]]:
    """
    Merge rows where first column is empty (continuation of previous row).
    
    Args:
        rows_data: List of row data (each row is list of cell values)
        
    Returns:
        Merged rows
    """
    if not rows_data:
        return []
    
    merged = [rows_data[0]]
    
    for row in rows_data[1:]:
        # If first column is empty or very short, merge with previous
        if not row[0] or len(row[0].strip()) < 3:
            # Merge into last row
            for i in range(len(row)):
                if row[i]:
                    if merged[-1][i]:
                        merged[-1][i] += ' ' + row[i]
                    else:
                        merged[-1][i] = row[i]
        else:
            # New row
            merged.append(row)
    
    return merged


def reconstruct_table(block_words: List[Dict]) -> Dict:
    """
    Main table reconstruction pipeline.
    
    Returns:
        {
            'headers': List[str],
            'rows': List[List[str]],
            'column_count': int
        }
    """
    # STEP 1: Cluster into rows
    rows = cluster_words_into_rows(block_words)
    
    if not rows:
        return {'headers': [], 'rows': [], 'column_count': 0}
    
    # STEP 2: Detect header
    header_idx, headers = detect_header_row(rows)
    
    if header_idx < 0 or header_idx >= len(rows):
        # Fallback: use first row as header
        header_idx = 0
        headers = [w['text'] for w in rows[0]]
    
    # STEP 3: Build column boundaries
    header_row = rows[header_idx]
    column_boundaries = build_column_boundaries(header_row)
    
    # STEP 4: Map all rows to grid
    data_rows = []
    for row_idx, row_words in enumerate(rows):
        if row_idx == header_idx:
            continue  # Skip header row
        
        cells = assign_words_to_columns(row_words, column_boundaries)
        data_rows.append(cells)
    
    # STEP 5: Merge multi-line cells
    data_rows = merge_multiline_cells(data_rows)
    
    return {
        'headers': headers,
        'rows': data_rows,
        'column_count': len(headers)
    }
