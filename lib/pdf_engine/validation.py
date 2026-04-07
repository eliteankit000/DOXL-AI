"""
DocXL AI - Validation & Correction Engine
Ensures data quality and consistency
"""
from typing import List
import re

def ensure_column_consistency(rows: List[List[str]], expected_columns: int) -> List[List[str]]:
    """
    Ensure all rows have same number of columns.
    Pad with empty strings or trim excess.
    """
    cleaned_rows = []
    
    for row in rows:
        if len(row) < expected_columns:
            # Pad with empty strings
            row = row + [''] * (expected_columns - len(row))
        elif len(row) > expected_columns:
            # Trim excess
            row = row[:expected_columns]
        
        cleaned_rows.append(row)
    
    return cleaned_rows


def clean_numeric_value(value: str) -> str:
    """
    Extract clean numeric value from text.
    Removes currency symbols, commas, and extra whitespace.
    """
    if not value:
        return ''
    
    # Remove common currency symbols and commas
    cleaned = re.sub(r'[₹$€£,]', '', value)
    cleaned = cleaned.strip()
    
    # Extract number pattern
    match = re.search(r'-?\d+\.?\d*', cleaned)
    if match:
        return match.group()
    
    return value  # Return original if no number found


def is_empty_row(row: List[str]) -> bool:
    """
    Check if row is empty or contains only whitespace.
    """
    return all(not cell.strip() for cell in row)


def is_noise_row(row: List[str]) -> bool:
    """
    Check if row is likely noise (very short text in all cells).
    """
    non_empty = [cell for cell in row if cell.strip()]
    if not non_empty:
        return True
    
    # If all non-empty cells are <= 2 chars, likely noise
    return all(len(cell.strip()) <= 2 for cell in non_empty)


def remove_empty_rows(rows: List[List[str]]) -> List[List[str]]:
    """
    Remove empty or noise rows.
    """
    return [row for row in rows if not is_empty_row(row) and not is_noise_row(row)]


def clean_numeric_columns(headers: List[str], rows: List[List[str]]) -> List[List[str]]:
    """
    Clean numeric values in amount/price/total columns.
    """
    # Detect numeric column indices
    numeric_keywords = ['amount', 'price', 'rate', 'total', 'cost', 'value', 'tax', 'cgst', 'sgst']
    numeric_indices = []
    
    for idx, header in enumerate(headers):
        if any(kw in header.lower() for kw in numeric_keywords):
            numeric_indices.append(idx)
    
    # Clean values in numeric columns
    cleaned_rows = []
    for row in rows:
        cleaned_row = row.copy()
        for idx in numeric_indices:
            if idx < len(cleaned_row):
                cleaned_row[idx] = clean_numeric_value(cleaned_row[idx])
        cleaned_rows.append(cleaned_row)
    
    return cleaned_rows


def validate_table_structure(headers: List[str], rows: List[List[str]]) -> bool:
    """
    Validate table has proper structure.
    
    Returns:
        True if valid, False otherwise
    """
    # Must have headers
    if not headers or len(headers) == 0:
        return False
    
    # Must have at least one data row
    if not rows or len(rows) == 0:
        return False
    
    # All rows must have same column count as headers
    for row in rows:
        if len(row) != len(headers):
            return False
    
    return True


def validate_and_clean_table(table_data: dict) -> dict:
    """
    Main validation pipeline.
    
    Args:
        table_data: {headers, rows, column_count}
        
    Returns:
        Cleaned table_data
    """
    headers = table_data.get('headers', [])
    rows = table_data.get('rows', [])
    column_count = len(headers)
    
    if not headers or not rows:
        return table_data
    
    # STEP 1: Ensure column consistency
    rows = ensure_column_consistency(rows, column_count)
    
    # STEP 2: Remove empty/noise rows
    rows = remove_empty_rows(rows)
    
    # STEP 3: Clean numeric columns
    rows = clean_numeric_columns(headers, rows)
    
    # STEP 4: Validate structure
    is_valid = validate_table_structure(headers, rows)
    
    return {
        'headers': headers,
        'rows': rows,
        'column_count': column_count,
        'is_valid': is_valid
    }
