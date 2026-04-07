#!/usr/bin/env python3
"""
DocXL AI — True Document Layout Reconstruction Engine v7.0
COORDINATE-BASED RENDERING (not just AI extraction)

Architecture:
PDF/Image → OCR+Layout (coordinates) → Row Grouping (Y) → Column Mapping (X) 
→ Block Detection → Grid Builder → Output
"""
import sys
import os
import json
import base64
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
if not OPENAI_API_KEY:
    print(json.dumps({"error": "OPENAI_API_KEY not configured"}))
    sys.exit(1)

LOG_STEPS = []

def log_step(step, msg):
    """Structured logging."""
    LOG_STEPS.append({"step": step, "msg": msg, "ts": time.time()})
    print(f'[{step}] {msg}', file=sys.stderr)

# ═══════════════════════════════════════════════════════════════════
# STAGE 1: COORDINATE EXTRACTION (OCR + Layout)
# ═══════════════════════════════════════════════════════════════════

def extract_coordinates_from_pdf(file_path: str) -> List[Dict]:
    """
    Extract text with coordinates using pdfplumber.
    Returns: [{text, x, y, width, height, page}]
    """
    import pdfplumber
    
    log_step("COORDINATES", f"Extracting coordinates from PDF: {file_path}")
    
    elements = []
    
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages[:10], start=1):  # Max 10 pages
            # Extract words with bounding boxes
            words = page.extract_words(
                x_tolerance=3,
                y_tolerance=3,
                keep_blank_chars=False,
                use_text_flow=True
            )
            
            for word in words:
                elements.append({
                    'text': word['text'],
                    'x': word['x0'],
                    'y': word['top'],
                    'width': word['x1'] - word['x0'],
                    'height': word['bottom'] - word['top'],
                    'page': page_num
                })
    
    log_step("COORDINATES", f"Extracted {len(elements)} text elements with coordinates")
    return elements

def extract_coordinates_from_image(file_path: str) -> List[Dict]:
    """
    Extract text with coordinates from image using GPT-4o Vision.
    Returns: [{text, x, y, width, height, page}]
    """
    from openai import OpenAI
    
    log_step("COORDINATES", f"Extracting coordinates from image: {file_path}")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    with open(file_path, 'rb') as f:
        img_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    prompt = """Extract ALL text from this image with approximate coordinates.

For each text element, estimate its position:
- x: horizontal position (0-100 scale, 0=left, 100=right)
- y: vertical position (0-100 scale, 0=top, 100=bottom)

Return ONLY JSON array:
[
  {"text": "Hotel Name", "x": 45, "y": 5, "width": 20, "height": 8},
  {"text": "Invoice No:", "x": 10, "y": 20, "width": 15, "height": 5},
  {"text": "12345", "x": 30, "y": 20, "width": 10, "height": 5}
]

Extract EVERY visible text element. Return coordinates in 0-100 scale."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                    }
                ]
            }
        ],
        max_tokens=8192,
        temperature=0.1
    )
    
    raw = response.choices[0].message.content.strip()
    
    # Extract JSON array
    import re
    json_match = re.search(r'\[.*\]', raw, re.DOTALL)
    if json_match:
        elements = json.loads(json_match.group())
        for elem in elements:
            elem['page'] = 1
            # Set defaults if missing
            elem.setdefault('width', 10)
            elem.setdefault('height', 5)
        
        log_step("COORDINATES", f"Extracted {len(elements)} elements from image")
        return elements
    
    log_step("COORDINATES_ERROR", "Failed to extract coordinates from image")
    return []

# ═══════════════════════════════════════════════════════════════════
# STAGE 2: ROW GROUPING (Y-AXIS CLUSTERING)
# ═══════════════════════════════════════════════════════════════════

def group_into_rows(elements: List[Dict], y_threshold: float = 5) -> List[List[Dict]]:
    """
    Group elements into rows based on Y coordinate proximity.
    Elements with similar Y values are in the same row.
    """
    log_step("ROW_GROUPING", f"Grouping {len(elements)} elements into rows")
    
    if not elements:
        return []
    
    # Sort by Y position first
    sorted_elements = sorted(elements, key=lambda e: e['y'])
    
    rows = []
    current_row = [sorted_elements[0]]
    current_y = sorted_elements[0]['y']
    
    for elem in sorted_elements[1:]:
        if abs(elem['y'] - current_y) <= y_threshold:
            # Same row
            current_row.append(elem)
        else:
            # New row
            rows.append(current_row)
            current_row = [elem]
            current_y = elem['y']
    
    # Add last row
    if current_row:
        rows.append(current_row)
    
    log_step("ROW_GROUPING", f"Created {len(rows)} rows")
    return rows

# ═══════════════════════════════════════════════════════════════════
# STAGE 3: COLUMN ORDERING (X-AXIS SORT)
# ═══════════════════════════════════════════════════════════════════

def sort_row_by_columns(row: List[Dict]) -> List[Dict]:
    """
    Sort elements in a row by X coordinate (left to right).
    """
    return sorted(row, key=lambda e: e['x'])

# ═══════════════════════════════════════════════════════════════════
# STAGE 4: COLUMN DETECTION (X-AXIS CLUSTERING)
# ═══════════════════════════════════════════════════════════════════

def detect_columns(rows: List[List[Dict]], x_threshold: float = 10) -> List[float]:
    """
    Detect column positions by finding common X coordinates across rows.
    Returns list of column X positions.
    """
    log_step("COLUMN_DETECTION", "Detecting column boundaries")
    
    # Collect all X positions
    all_x = []
    for row in rows:
        for elem in row:
            all_x.append(elem['x'])
    
    if not all_x:
        return [0]
    
    # Cluster X positions
    all_x.sort()
    columns = [all_x[0]]
    
    for x in all_x[1:]:
        if x - columns[-1] > x_threshold:
            columns.append(x)
    
    log_step("COLUMN_DETECTION", f"Detected {len(columns)} column boundaries")
    return columns

def assign_column_index(x: float, columns: List[float], threshold: float = 10) -> int:
    """
    Assign element to nearest column index.
    """
    for i, col_x in enumerate(columns):
        if abs(x - col_x) <= threshold:
            return i
    
    # Find closest column
    distances = [abs(x - col_x) for col_x in columns]
    return distances.index(min(distances))

# ═══════════════════════════════════════════════════════════════════
# STAGE 5: GRID BUILDER
# ═══════════════════════════════════════════════════════════════════

def build_grid(rows: List[List[Dict]], columns: List[float]) -> List[Dict]:
    """
    Build Excel grid cells from positioned rows and columns.
    Returns: [{row, col, value, merge, style}]
    """
    log_step("GRID_BUILDER", f"Building grid from {len(rows)} rows")
    
    cells = []
    
    for row_idx, row in enumerate(rows, start=1):
        # Sort elements in row by X
        sorted_row = sort_row_by_columns(row)
        
        # Track which columns are used in this row
        col_usage = {}
        
        for elem in sorted_row:
            col_idx = assign_column_index(elem['x'], columns)
            
            # Merge adjacent text in same column
            if col_idx in col_usage:
                # Append to existing cell
                cells[col_usage[col_idx]]['value'] += ' ' + elem['text']
            else:
                # New cell
                cell = {
                    'row': row_idx,
                    'col': col_idx + 1,  # 1-based
                    'value': elem['text']
                }
                
                # Detect styles
                style = {}
                
                # Bold detection (heuristic: ALL CAPS or first row)
                if elem['text'].isupper() and len(elem['text']) > 2:
                    style['bold'] = True
                if row_idx == 1:
                    style['bold'] = True
                
                # Alignment detection
                if elem['x'] > 70:  # Right side
                    style['align'] = 'right'
                elif 40 < elem['x'] < 60:  # Center
                    style['align'] = 'center'
                
                if style:
                    cell['style'] = style
                
                cells.append(cell)
                col_usage[col_idx] = len(cells) - 1
    
    log_step("GRID_BUILDER", f"Built {len(cells)} cells")
    return cells

# ═══════════════════════════════════════════════════════════════════
# STAGE 6: MERGE DETECTION
# ═══════════════════════════════════════════════════════════════════

def detect_merges(cells: List[Dict], columns: List[float]) -> List[Dict]:
    """
    Detect cells that should span multiple columns.
    Modifies cells in place to add 'merge' property.
    """
    log_step("MERGE_DETECTION", "Detecting merged cells")
    
    # Group cells by row
    rows_dict = defaultdict(list)
    for cell in cells:
        rows_dict[cell['row']].append(cell)
    
    merge_count = 0
    
    for row_num, row_cells in rows_dict.items():
        if len(row_cells) == 1 and len(columns) > 1:
            # Single cell in row with multiple columns → likely merged header
            cell = row_cells[0]
            cell['merge'] = [1, len(columns)]  # Span all columns
            merge_count += 1
    
    log_step("MERGE_DETECTION", f"Detected {merge_count} merged cells")
    return cells

# ═══════════════════════════════════════════════════════════════════
# STAGE 7: MULTI-PAGE ASSEMBLY
# ═══════════════════════════════════════════════════════════════════

def assemble_pages(elements: List[Dict]) -> Dict:
    """
    Assemble multi-page document into sheets.
    Returns: {sheets: [{name, cells}]}
    """
    log_step("ASSEMBLY", "Assembling pages into sheets")
    
    # Group elements by page
    pages = defaultdict(list)
    for elem in elements:
        pages[elem['page']].append(elem)
    
    sheets = []
    
    for page_num in sorted(pages.keys()):
        page_elements = pages[page_num]
        
        # Process this page
        rows = group_into_rows(page_elements)
        columns = detect_columns(rows)
        cells = build_grid(rows, columns)
        cells = detect_merges(cells, columns)
        
        sheet = {
            'name': f'Page {page_num}',
            'max_row': len(rows),
            'max_col': len(columns),
            'cells': cells
        }
        
        sheets.append(sheet)
    
    result = {
        'document_type': 'layout_preserved',
        'pages': len(sheets),
        'sheets': sheets,
        'confidence': 0.95,
        'extraction_method': 'coordinate_based_v7'
    }
    
    log_step("ASSEMBLY", f"Assembled {len(sheets)} sheet(s)")
    return result

# ═══════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python extract.py <file_path> [user_requirements]"}))
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)
    
    file_ext = Path(file_path).suffix.lower()
    
    try:
        start_time = time.time()
        
        # STAGE 1: Extract coordinates
        if file_ext == '.pdf':
            elements = extract_coordinates_from_pdf(file_path)
        else:
            elements = extract_coordinates_from_image(file_path)
        
        if not elements:
            raise ValueError("No text elements extracted")
        
        # STAGES 2-7: Build grid and assemble
        result = assemble_pages(elements)
        
        elapsed = time.time() - start_time
        log_step("COMPLETE", f"Processing completed in {elapsed:.2f}s")
        
        print(json.dumps(result, indent=2))
    
    except Exception as e:
        log_step("FATAL_ERROR", str(e))
        print(json.dumps({
            "error": str(e),
            "document_type": "unknown",
            "sheets": [],
            "confidence": 0.0
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
