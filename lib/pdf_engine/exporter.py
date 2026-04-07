"""
DocXL AI - Excel Exporter
Converts table data to Excel format
"""
from typing import List, Dict
import pandas as pd

def table_to_dataframe(table_data: dict) -> pd.DataFrame:
    """
    Convert table data to pandas DataFrame.
    
    Args:
        table_data: {headers, rows}
        
    Returns:
        pandas DataFrame
    """
    headers = table_data.get('headers', [])
    rows = table_data.get('rows', [])
    
    if not headers or not rows:
        return pd.DataFrame()
    
    # Create DataFrame
    df = pd.DataFrame(rows, columns=headers)
    
    return df


def convert_to_output_format(table_data: dict) -> dict:
    """
    Convert table data to frontend/API output format.
    
    Returns:
        {
            'columns': List[str],
            'rows': List[Dict],
            'document_type': str,
            'confidence': float
        }
    """
    headers = table_data.get('headers', [])
    rows = table_data.get('rows', [])
    
    # Convert rows to list of dictionaries
    row_dicts = []
    for row in rows:
        row_dict = {}
        for idx, header in enumerate(headers):
            value = row[idx] if idx < len(row) else ''
            row_dict[header] = value
        row_dicts.append(row_dict)
    
    return {
        'columns': headers,
        'rows': row_dicts,
        'document_type': 'table',
        'confidence': 0.95,
        'extraction_method': 'pymupdf_algorithmic'
    }


def export_to_excel_buffer(table_data: dict) -> bytes:
    """
    Export table to Excel bytes buffer.
    
    Returns:
        Excel file as bytes
    """
    df = table_to_dataframe(table_data)
    
    if df.empty:
        return b''
    
    # Convert to Excel bytes
    from io import BytesIO
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Extracted Data')
    
    buffer.seek(0)
    return buffer.getvalue()
