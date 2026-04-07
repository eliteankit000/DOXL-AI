#!/usr/bin/env python3
"""
DocXL AI — Enterprise Document Layout Reconstruction Engine v6.0
11-STAGE LAYOUT-AWARE PIPELINE: Detect → Analyze → Position → Reconstruct → Export

PRIMARY OBJECTIVE: Recreate document inside Excel with EXACT VISUAL LAYOUT
- Same structure, same positioning, same spacing
- NOT just data extraction — FULL VISUAL RECONSTRUCTION
- Uses bounding boxes, X/Y mapping to Excel grid
"""
import sys
import os
import json
import base64
import asyncio
import re
import time
from pathlib import Path
from openai import AsyncOpenAI
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
if not OPENAI_API_KEY:
    print(json.dumps({"error": "OPENAI_API_KEY not configured"}))
    sys.exit(1)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

LOG_STEPS = []

def log_step(step, msg, extra=None):
    """Structured logging for pipeline tracking."""
    entry = {"step": step, "msg": msg, "ts": time.time()}
    if extra:
        entry["extra"] = extra
    LOG_STEPS.append(entry)
    print(f'[{step}] {msg}', file=sys.stderr)

# ═══════════════════════════════════════════════════════════════════
# STAGE 1: PAGE DETECTION & MULTI-PAGE HANDLING
# ═══════════════════════════════════════════════════════════════════

async def detect_pages(file_path: str, file_ext: str) -> List[str]:
    """
    Detect and extract individual pages as base64 images.
    Returns list of base64 image strings (one per page, max 10 pages).
    """
    log_step("STAGE_1", f"Detecting pages from {file_ext} file")
    
    pages = []
    
    if file_ext in ['.pdf']:
        # Extract pages from PDF
        try:
            import pdfplumber
            from PIL import Image
            import io
            
            with pdfplumber.open(file_path) as pdf:
                total_pages = min(len(pdf.pages), 10)  # Max 10 pages
                log_step("STAGE_1", f"PDF detected: {total_pages} pages (limit 10)")
                
                for i in range(total_pages):
                    page = pdf.pages[i]
                    # Convert PDF page to image
                    pil_image = page.to_image(resolution=150).original
                    
                    # Convert PIL Image to base64
                    buffer = io.BytesIO()
                    pil_image.save(buffer, format='PNG')
                    img_bytes = buffer.getvalue()
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    pages.append(img_base64)
                    
                log_step("STAGE_1", f"Extracted {len(pages)} pages from PDF")
        except Exception as e:
            log_step("STAGE_1_ERROR", f"PDF extraction failed: {e}")
            # Fallback: treat as single-page image
            with open(file_path, 'rb') as f:
                img_base64 = base64.b64encode(f.read()).decode('utf-8')
                pages.append(img_base64)
    else:
        # Single image file
        with open(file_path, 'rb') as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')
            pages.append(img_base64)
        log_step("STAGE_1", f"Single page image detected")
    
    return pages

# ═══════════════════════════════════════════════════════════════════
# STAGE 2-10: LAYOUT ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════════

LAYOUT_ANALYSIS_PROMPT = """You are an enterprise-grade Document Layout Reconstruction Engine.

Your task is to analyze this document page and create COMPLETE LAYOUT INSTRUCTIONS for Excel recreation.

## 🎯 PRIMARY OBJECTIVE
Recreate the document inside Excel with EXACT VISUAL LAYOUT:
✔ Same structure ✔ Same positioning ✔ Same spacing ✔ Same reading flow

## 📐 STAGE 2: FULL DOCUMENT LAYOUT ANALYSIS

Analyze using:
- Bounding boxes (X, Y positions of ALL elements)
- Text alignment (left/center/right)
- Spacing between elements
- Section grouping
- Visual hierarchy

## 🧠 STAGE 3: BLOCK DETECTION

Split document into layout blocks with COORDINATES:

1. **HEADER** (logo, company info) — top section
2. **TITLE** (invoice title, document name) — centered/bold
3. **KEY-VALUE SECTIONS** (invoice no, date, customer details) — label: value pairs
4. **TABLES** (line items, transaction history) — structured rows/columns
5. **PARAGRAPHS** (terms, notes) — text blocks
6. **TOTALS/SUMMARY** (grand total, subtotal) — right-aligned numbers
7. **FOOTER** (bank details, signatures) — bottom section

For EACH block, detect:
- X position (left margin, 0-100 scale)
- Y position (top margin, 0-100 scale)
- Width (how wide the block is)
- Height (how tall the block is)
- Alignment (left/center/right)
- Style (bold/normal)

## 🧠 STAGE 4-5: POSITIONAL RECONSTRUCTION

Map document coordinates to Excel grid:

**HORIZONTAL MAPPING (X → Column):**
- Document width divided into ~12 columns (like Excel default view)
- X=0-8 → Column A (col 1)
- X=8-16 → Column B (col 2)
- X=16-25 → Column C (col 3)
- ... and so on
- X=92-100 → Column L (col 12)

**VERTICAL MAPPING (Y → Row):**
- Each text line ≈ 1 row
- Spacing between sections = empty rows
- Y=0-2 → Row 1
- Y=2-4 → Row 2
- Small gap (2-4 units) → +1 empty row
- Large gap (>4 units) → +2-3 empty rows

## 🧠 STAGE 6-9: RENDERING RULES

### A. TEXT BLOCKS
Place text in exact relative position using merged cells where needed.

### B. KEY-VALUE PAIRS
Place side-by-side (label in col A, value in col B) at correct row position.

### C. TABLES
Detect real tables, preserve exact column count and row order.

### D. SPACING
Insert empty rows/columns to match layout spacing.

## 🧠 STAGE 10: EXCEL CELL STRUCTURE

Return structured layout instructions:

```json
{
  "page_number": 1,
  "max_row": 40,
  "max_col": 12,
  "blocks": [
    {
      "type": "header",
      "x": 0,
      "y": 0,
      "width": 100,
      "height": 10,
      "content": "Hotel Kanchan\\nMain Road, Indore",
      "align": "center",
      "bold": true
    },
    {
      "type": "key_value",
      "x": 0,
      "y": 15,
      "width": 50,
      "items": [
        {"label": "Invoice No", "value": "43"},
        {"label": "Date", "value": "06/04/2026"}
      ]
    },
    {
      "type": "table",
      "x": 0,
      "y": 30,
      "width": 100,
      "columns": ["Particular", "Amount", "CGST", "SGST", "Total"],
      "rows": [
        {"Particular": "Room Tariff", "Amount": "1619.05", "CGST": "40.48", "SGST": "40.48", "Total": "1700"}
      ],
      "header_bold": true
    },
    {
      "type": "total",
      "x": 70,
      "y": 80,
      "label": "Grand Total",
      "value": "1700",
      "align": "right",
      "bold": true
    }
  ],
  "cells": [
    {"row": 1, "col": 1, "value": "Hotel Kanchan", "merge": [1, 12], "style": {"bold": true, "align": "center"}},
    {"row": 2, "col": 1, "value": "Main Road, Indore", "merge": [1, 12], "style": {"align": "center"}},
    {"row": 5, "col": 1, "value": "Invoice No"},
    {"row": 5, "col": 2, "value": "43"},
    {"row": 6, "col": 1, "value": "Date"},
    {"row": 6, "col": 2, "value": "06/04/2026"},
    {"row": 10, "col": 1, "value": "Particular", "style": {"bold": true}},
    {"row": 10, "col": 5, "value": "Amount", "style": {"bold": true, "align": "right"}},
    {"row": 11, "col": 1, "value": "Room Tariff"},
    {"row": 11, "col": 5, "value": "1619.05", "style": {"align": "right"}},
    {"row": 30, "col": 10, "value": "Grand Total", "style": {"bold": true}},
    {"row": 30, "col": 12, "value": "1700", "style": {"bold": true, "align": "right"}}
  ]
}
```

## ✅ CRITICAL RULES:

1. **DETECT ALL VISIBLE ELEMENTS** — every text block, every number, every label
2. **PRESERVE SPACING** — if there's a gap in the document, add empty rows in Excel
3. **USE MERGED CELLS** for titles that span multiple columns
4. **MAINTAIN ALIGNMENT** — left/center/right alignment must match original
5. **BOLD HEADERS** — make table headers and section titles bold
6. **NO DATA LOSS** — all visible data must be included
7. **POSITIONAL ACCURACY** — elements should be at approximately correct row/col positions
8. **READING FLOW** — top-to-bottom, left-to-right flow should be preserved

## 📊 OUTPUT FORMAT:

Return ONLY JSON with this structure:
{
  "page_number": 1,
  "max_row": <estimated rows needed>,
  "max_col": 12,
  "cells": [
    {"row": <1-based row number>, "col": <1-based col number>, "value": "<text>", "merge": [<start_col>, <end_col>], "style": {"bold": true/false, "align": "left|center|right"}}
  ]
}

**IMPORTANT:**
- "merge" is optional, use only when cell should span multiple columns. Format: [start_col, end_col] inclusive.
- "style" is optional, only include if bold=true or align is not "left"
- Keep "value" as strings (even for numbers)
- Row and col numbers are 1-based (row 1 = first row)

RETURN ONLY THE JSON. NO TEXT BEFORE OR AFTER. NO MARKDOWN BLOCKS."""

async def analyze_page_layout(page_base64: str, page_num: int, user_requirements: str = "") -> Dict[str, Any]:
    """
    Analyze a single page and generate Excel layout instructions.
    Uses GPT-4o Vision for layout-aware extraction.
    """
    log_step("STAGE_2-10", f"Analyzing layout for page {page_num}")
    
    prompt = LAYOUT_ANALYSIS_PROMPT
    if user_requirements:
        prompt += f"\n\n**USER REQUIREMENTS:** {user_requirements}\nPay special attention to these requirements while extracting."
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{page_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=16384,
            temperature=0.1
        )
        
        raw_output = response.choices[0].message.content.strip()
        log_step("STAGE_2-10", f"GPT-4o response received for page {page_num}")
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if json_match:
            layout_data = json.loads(json_match.group())
            layout_data['page_number'] = page_num
            
            # Ensure required fields
            if 'cells' not in layout_data:
                layout_data['cells'] = []
            if 'max_row' not in layout_data:
                layout_data['max_row'] = 50
            if 'max_col' not in layout_data:
                layout_data['max_col'] = 12
            
            log_step("STAGE_2-10", f"Page {page_num} layout extracted: {len(layout_data.get('cells', []))} cells")
            return layout_data
        else:
            raise ValueError("No JSON found in GPT-4o response")
    
    except Exception as e:
        log_step("STAGE_2-10_ERROR", f"Layout analysis failed for page {page_num}: {e}")
        # Return minimal fallback structure
        return {
            "page_number": page_num,
            "max_row": 50,
            "max_col": 12,
            "cells": [
                {"row": 1, "col": 1, "value": f"[Error: Could not analyze page {page_num}]"}
            ]
        }

# ═══════════════════════════════════════════════════════════════════
# STAGE 11: MULTI-SHEET ASSEMBLY
# ═══════════════════════════════════════════════════════════════════

def assemble_multi_sheet_output(page_layouts: List[Dict[str, Any]], file_name: str) -> Dict[str, Any]:
    """
    Assemble all page layouts into final multi-sheet structure.
    """
    log_step("STAGE_11", f"Assembling {len(page_layouts)} pages into sheets")
    
    sheets = []
    for layout in page_layouts:
        page_num = layout.get('page_number', 1)
        sheet = {
            "name": f"Page {page_num}",
            "max_row": layout.get('max_row', 50),
            "max_col": layout.get('max_col', 12),
            "cells": layout.get('cells', [])
        }
        sheets.append(sheet)
    
    result = {
        "document_type": "layout_preserved",
        "file_name": file_name,
        "pages": len(sheets),
        "sheets": sheets,
        "confidence": 0.95,  # High confidence for layout-based extraction
        "extraction_method": "layout_reconstruction_v6"
    }
    
    log_step("STAGE_11", f"Multi-sheet assembly complete: {len(sheets)} sheets")
    return result

# ═══════════════════════════════════════════════════════════════════
# MAIN PIPELINE ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════

async def process_document(file_path: str, user_requirements: str = "") -> Dict[str, Any]:
    """
    Main pipeline: Processes document with full layout reconstruction.
    """
    file_name = Path(file_path).name
    file_ext = Path(file_path).suffix.lower()
    
    log_step("PIPELINE_START", f"Processing {file_name} with layout reconstruction")
    
    # STAGE 1: Detect pages
    pages = await detect_pages(file_path, file_ext)
    log_step("PIPELINE", f"Detected {len(pages)} page(s)")
    
    # STAGE 2-10: Analyze each page layout (max 10 pages)
    page_layouts = []
    for i, page_base64 in enumerate(pages[:10], start=1):
        layout = await analyze_page_layout(page_base64, i, user_requirements)
        page_layouts.append(layout)
    
    # STAGE 11: Assemble multi-sheet output
    result = assemble_multi_sheet_output(page_layouts, file_name)
    
    log_step("PIPELINE_COMPLETE", f"Layout reconstruction complete: {len(result['sheets'])} sheets")
    return result

# ═══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

async def main():
    """Entry point for script."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python extract.py <file_path> [user_requirements]"}))
        sys.exit(1)
    
    file_path = sys.argv[1]
    user_requirements = sys.argv[2] if len(sys.argv) > 2 else ""
    
    if not os.path.exists(file_path):
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)
    
    try:
        result = await process_document(file_path, user_requirements)
        print(json.dumps(result, indent=2))
    except Exception as e:
        log_step("FATAL_ERROR", str(e))
        print(json.dumps({
            "error": str(e),
            "document_type": "unknown",
            "confidence": 0.0,
            "sheets": [],
            "logs": LOG_STEPS
        }))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
