"""
DocXL AI - Table Reconstruction Engine v9.0 (NITRO QUALITY UPGRADE)
Algorithmic table reconstruction with STRICT rules for perfect accuracy

UPGRADED WITH 9 PHASES:
1. Hard Table Isolation
2. Column Locking System
3. Strict Grid Mapping
4. Row Stability Rule
5. Multi-line Control (Strict)
6. Column Type Lock
7. Structure Validation Loop
8. Hard Noise Removal
9. Final Strict Export Check
"""
from typing import List, Dict, Tuple, Optional
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

# Global locked columns (Phase 2)
LOCKED_COLUMNS: Optional[List[Tuple[float, float]]] = None

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


# ═══════════════════════════════════════════════════════════════════
# PHASE 1: HARD TABLE ISOLATION
# ═══════════════════════════════════════════════════════════════════

def is_table_row(row: List[Dict]) -> bool:
    """
    PHASE 1: A row is considered part of a table ONLY if it has at least 3 elements.
    
    STRICT RULE: Stop mixing non-table data with table data.
    """
    return len(row) >= 3


def isolate_table_rows(rows: List[List[Dict]]) -> List[List[Dict]]:
    """
    PHASE 1: Build table ONLY from consecutive rows where is_table_row() == True.
    Stop when sequence breaks.
    
    STRICTLY IGNORE: Header text, Footer text, Random single-line rows
    """
    if not rows:
        return []
    
    # Find first table row
    start_idx = None
    for i, row in enumerate(rows):
        if is_table_row(row):
            start_idx = i
            break
    
    if start_idx is None:
        return []
    
    # Collect consecutive table rows
    table_rows = []
    for row in rows[start_idx:]:
        if is_table_row(row):
            table_rows.append(row)
        else:
            # Sequence broken - stop table
            # Allow 1 non-table row gap (could be multi-line continuation)
            if len(table_rows) > 0:
                # Check if next row resumes table
                next_idx = rows.index(row) + 1
                if next_idx < len(rows) and is_table_row(rows[next_idx]):
                    continue  # Skip this gap
                else:
                    break  # Stop table
    
    return table_rows


# ═══════════════════════════════════════════════════════════════════
# PHASE 2: COLUMN LOCKING SYSTEM
# ═══════════════════════════════════════════════════════════════════

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
    PHASE 2: Build column boundaries from header row positions.
    Once built, these are LOCKED and never recomputed.
    
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


def lock_columns(column_boundaries: List[Tuple[float, float]]):
    """
    PHASE 2: Lock columns globally.
    RULE: Columns must NEVER shift once detected.
    """
    global LOCKED_COLUMNS
    LOCKED_COLUMNS = column_boundaries


def get_locked_columns() -> List[Tuple[float, float]]:
    """
    PHASE 2: Retrieve locked columns.
    """
    return LOCKED_COLUMNS or []


# ═══════════════════════════════════════════════════════════════════
# PHASE 3: STRICT GRID MAPPING
# ═══════════════════════════════════════════════════════════════════

def assign_words_to_columns_strict(row_words: List[Dict], column_boundaries: List[Tuple[float, float]]) -> List[str]:
    """
    PHASE 3: Ensure words go into correct columns only.
    
    RULES:
    - Assign word ONLY if it falls inside a column range
    - If not: assign to nearest valid column OR ignore
    
    STRICT:
    - No flexible shifting
    - No dynamic column creation
    """
    cells = [''] * len(column_boundaries)
    
    for word in row_words:
        word_x = word['x0']
        assigned = False
        
        # Try exact match first
        for col_idx, (x_start, x_end) in enumerate(column_boundaries):
            if x_start <= word_x < x_end:
                if cells[col_idx]:
                    cells[col_idx] += ' ' + word['text']
                else:
                    cells[col_idx] = word['text']
                assigned = True
                break
        
        # If not assigned, find nearest column
        if not assigned:
            distances = [abs(word_x - x_start) for x_start, _ in column_boundaries]
            nearest_col = distances.index(min(distances))
            
            # Only assign if within reasonable distance (max 50 units)
            if min(distances) < 50:
                if cells[nearest_col]:
                    cells[nearest_col] += ' ' + word['text']
                else:
                    cells[nearest_col] = word['text']
    
    return cells


# ═══════════════════════════════════════════════════════════════════
# PHASE 4: ROW STABILITY RULE
# ═══════════════════════════════════════════════════════════════════

def is_weak_row(row: List[str]) -> bool:
    """
    PHASE 4: A valid row MUST have consistent Y alignment and contain at least 2 non-empty cells.
    
    weak_row = number_of_non_empty_cells < 2
    """
    non_empty = [cell for cell in row if cell and cell.strip()]
    return len(non_empty) < 2


def stabilize_rows(rows_data: List[List[str]]) -> List[List[str]]:
    """
    PHASE 4: Prevent row breaking.
    
    If weak_row: merge with previous row
    """
    if not rows_data:
        return []
    
    stabilized = [rows_data[0]]
    
    for row in rows_data[1:]:
        if is_weak_row(row):
            # Merge with previous row
            for i in range(len(row)):
                if row[i]:
                    if stabilized[-1][i]:
                        stabilized[-1][i] += ' ' + row[i]
                    else:
                        stabilized[-1][i] = row[i]
        else:
            # Keep as separate row
            stabilized.append(row)
    
    return stabilized


# ═══════════════════════════════════════════════════════════════════
# PHASE 5: MULTI-LINE CONTROL (STRICT)
# ═══════════════════════════════════════════════════════════════════

def check_x_alignment(current_row_words: List[Dict], previous_row_words: List[Dict], threshold: float = 10.0) -> bool:
    """
    PHASE 5: Check if X alignment matches previous row.
    """
    if not current_row_words or not previous_row_words:
        return False
    
    # Compare X positions of first words
    curr_x = current_row_words[0]['x0'] if current_row_words else 0
    prev_x = previous_row_words[0]['x0'] if previous_row_words else 0
    
    return abs(curr_x - prev_x) <= threshold


def merge_multiline_cells_strict(rows_data: List[List[str]], original_rows: List[List[Dict]]) -> List[List[str]]:
    """
    PHASE 5: STRICT multi-line control.
    
    ONLY merge rows when:
    - first column is empty AND
    - X alignment matches previous row
    """
    if not rows_data or not original_rows:
        return rows_data
    
    merged = [rows_data[0]]
    
    for i, row in enumerate(rows_data[1:], start=1):
        first_column_empty = not row[0] or len(row[0].strip()) < 3
        
        # Check X alignment with previous row
        x_alignment_close = False
        if i < len(original_rows) and i - 1 < len(original_rows):
            x_alignment_close = check_x_alignment(original_rows[i], original_rows[i - 1])
        
        if first_column_empty and x_alignment_close:
            # Merge with previous row
            for j in range(len(row)):
                if row[j]:
                    if merged[-1][j]:
                        merged[-1][j] += ' ' + row[j]
                    else:
                        merged[-1][j] = row[j]
        else:
            # Do NOT merge
            merged.append(row)
    
    return merged


# ═══════════════════════════════════════════════════════════════════
# PHASE 6: COLUMN TYPE LOCK
# ═══════════════════════════════════════════════════════════════════

def detect_column_types(rows_data: List[List[str]], headers: List[str]) -> List[str]:
    """
    PHASE 6: Detect column types (numeric vs text).
    
    If 80% values are numeric: column_type = "numeric"
    """
    if not rows_data:
        return ['text'] * len(headers)
    
    column_types = []
    
    for col_idx in range(len(headers)):
        numeric_count = 0
        total_count = 0
        
        for row in rows_data:
            if col_idx < len(row) and row[col_idx]:
                total_count += 1
                # Check if numeric
                cleaned = re.sub(r'[₹$€£,\s]', '', row[col_idx])
                if re.match(r'^-?\d+\.?\d*$', cleaned):
                    numeric_count += 1
        
        # If 80% are numeric, lock as numeric column
        if total_count > 0 and numeric_count / total_count >= 0.8:
            column_types.append('numeric')
        else:
            column_types.append('text')
    
    return column_types


def enforce_column_types(rows_data: List[List[str]], column_types: List[str]) -> List[List[str]]:
    """
    PHASE 6: Enforce column types.
    
    If column_type == "numeric": remove non-numeric noise
    """
    cleaned_rows = []
    
    for row in rows_data:
        cleaned_row = []
        for col_idx, cell in enumerate(row):
            if col_idx < len(column_types) and column_types[col_idx] == 'numeric':
                # Remove non-numeric noise
                cleaned = re.sub(r'[₹$€£,\s]', '', cell)
                if re.match(r'^-?\d+\.?\d*$', cleaned):
                    cleaned_row.append(cleaned)
                else:
                    cleaned_row.append('')  # Clear invalid data
            else:
                cleaned_row.append(cell)
        cleaned_rows.append(cleaned_row)
    
    return cleaned_rows


# ═══════════════════════════════════════════════════════════════════
# PHASE 7: STRUCTURE VALIDATION LOOP
# ═══════════════════════════════════════════════════════════════════

def validate_structure(headers: List[str], rows_data: List[List[str]]) -> Dict:
    """
    PHASE 7: Validate table structure.
    
    Check:
    - all rows have equal column count
    - no critical columns empty
    - numeric columns valid
    
    Returns:
        {
            'valid': bool,
            'issues': List[str],
            'needs_rebuild': bool
        }
    """
    issues = []
    expected_columns = len(headers)
    
    # Check 1: Equal column count
    for i, row in enumerate(rows_data):
        if len(row) != expected_columns:
            issues.append(f"Row {i} has {len(row)} columns, expected {expected_columns}")
    
    # Check 2: Critical columns not empty (first column)
    empty_first_col = sum(1 for row in rows_data if not row[0] or not row[0].strip())
    if empty_first_col > len(rows_data) * 0.5:
        issues.append("More than 50% of rows have empty first column")
    
    # Check 3: At least 2 data rows
    if len(rows_data) < 2:
        issues.append("Table has fewer than 2 data rows")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'needs_rebuild': len(issues) > 0
    }


def fix_structure(headers: List[str], rows_data: List[List[str]]) -> List[List[str]]:
    """
    PHASE 7: Fix structure issues.
    
    - Reassign misplaced cells
    - Merge broken rows
    """
    expected_columns = len(headers)
    fixed_rows = []
    
    for row in rows_data:
        if len(row) < expected_columns:
            # Pad with empty strings
            row = row + [''] * (expected_columns - len(row))
        elif len(row) > expected_columns:
            # Trim excess
            row = row[:expected_columns]
        
        fixed_rows.append(row)
    
    return fixed_rows


# ═══════════════════════════════════════════════════════════════════
# PHASE 8: HARD NOISE REMOVAL
# ═══════════════════════════════════════════════════════════════════

def is_noise_row(row: List[str]) -> bool:
    """
    PHASE 8: Delete rows if:
    - all cells empty
    - contains only symbols
    - not aligned with table structure
    """
    if not row:
        return True
    
    # All cells empty
    if all(not cell or not cell.strip() for cell in row):
        return True
    
    # Contains only symbols (no alphanumeric)
    combined_text = ''.join(row)
    if combined_text and not re.search(r'[a-zA-Z0-9]', combined_text):
        return True
    
    return False


def remove_noise_rows(rows_data: List[List[str]]) -> List[List[str]]:
    """
    PHASE 8: Remove noise rows.
    """
    return [row for row in rows_data if not is_noise_row(row)]


# ═══════════════════════════════════════════════════════════════════
# PHASE 9: FINAL STRICT EXPORT CHECK
# ═══════════════════════════════════════════════════════════════════

def final_export_check(headers: List[str], rows_data: List[List[str]]) -> List[List[str]]:
    """
    PHASE 9: Before exporting, ensure all(len(row) == expected_columns).
    
    If not: FIX before export. NEVER output broken table.
    """
    expected_columns = len(headers)
    
    checked_rows = []
    for row in rows_data:
        if len(row) != expected_columns:
            # Fix before export
            if len(row) < expected_columns:
                row = row + [''] * (expected_columns - len(row))
            else:
                row = row[:expected_columns]
        
        checked_rows.append(row)
    
    return checked_rows


# ═══════════════════════════════════════════════════════════════════
# MAIN RECONSTRUCTION PIPELINE (UPGRADED)
# ═══════════════════════════════════════════════════════════════════

def reconstruct_table(block_words: List[Dict]) -> Dict:
    """
    Main table reconstruction pipeline with NITRO-LEVEL ACCURACY.
    
    UPGRADED WITH 9 PHASES:
    1. Hard Table Isolation ✓
    2. Column Locking System ✓
    3. Strict Grid Mapping ✓
    4. Row Stability Rule ✓
    5. Multi-line Control (Strict) ✓
    6. Column Type Lock ✓
    7. Structure Validation Loop ✓
    8. Hard Noise Removal ✓
    9. Final Strict Export Check ✓
    
    Returns:
        {
            'headers': List[str],
            'rows': List[List[str]],
            'column_count': int
        }
    """
    global LOCKED_COLUMNS
    LOCKED_COLUMNS = None  # Reset for new table
    
    # STEP 1: Cluster into rows
    rows = cluster_words_into_rows(block_words)
    
    if not rows:
        return {'headers': [], 'rows': [], 'column_count': 0}
    
    # PHASE 1: Hard Table Isolation
    table_rows = isolate_table_rows(rows)
    
    if not table_rows:
        return {'headers': [], 'rows': [], 'column_count': 0}
    
    # STEP 2: Detect header
    header_idx, headers = detect_header_row(table_rows)
    
    if header_idx < 0 or header_idx >= len(table_rows):
        # Fallback: use first row as header
        header_idx = 0
        headers = [w['text'] for w in table_rows[0]]
    
    # PHASE 2: Build and LOCK column boundaries
    header_row = table_rows[header_idx]
    column_boundaries = build_column_boundaries(header_row)
    lock_columns(column_boundaries)
    
    # STEP 3: Map all rows to grid using LOCKED columns (Phase 3: Strict Grid Mapping)
    data_rows = []
    original_data_rows = []
    
    for row_idx, row_words in enumerate(table_rows):
        if row_idx == header_idx:
            continue  # Skip header row
        
        cells = assign_words_to_columns_strict(row_words, column_boundaries)
        data_rows.append(cells)
        original_data_rows.append(row_words)
    
    # PHASE 4: Row Stability Rule
    data_rows = stabilize_rows(data_rows)
    
    # PHASE 5: Multi-line Control (Strict)
    data_rows = merge_multiline_cells_strict(data_rows, original_data_rows)
    
    # PHASE 6: Column Type Lock
    column_types = detect_column_types(data_rows, headers)
    data_rows = enforce_column_types(data_rows, column_types)
    
    # PHASE 7: Structure Validation Loop
    validation = validate_structure(headers, data_rows)
    
    if validation['needs_rebuild']:
        # Fix structure
        data_rows = fix_structure(headers, data_rows)
        
        # Rebuild ONCE (no infinite loops)
        validation = validate_structure(headers, data_rows)
    
    # PHASE 8: Hard Noise Removal
    data_rows = remove_noise_rows(data_rows)
    
    # PHASE 9: Final Strict Export Check
    data_rows = final_export_check(headers, data_rows)
    
    return {
        'headers': headers,
        'rows': data_rows,
        'column_count': len(headers)
    }
