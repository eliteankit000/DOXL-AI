#!/usr/bin/env python3
"""
DocXL AI — Production Extraction Engine v4.0 (DYNAMIC COLUMNS)
NO PREDEFINED SCHEMA - columns detected from document structure
Target: 90-95% accuracy, ZERO failures, DYNAMIC column detection
Uses OpenAI GPT-4o directly
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

# ═══════════════════════════════════════════════════════
# STEP 1: DYNAMIC COLUMN DETECTION
# ═══════════════════════════════════════════════════════

# Universal prompt for ANY document type with dynamic columns
UNIVERSAL_PROMPT = """You are an expert data extraction AI.

TASK: Extract ALL data from this document into a structured table format.

CRITICAL RULES:
1. **AUTO-DETECT COLUMNS**: Look at the document and identify what columns exist
2. **NO PREDEFINED SCHEMA**: Do NOT assume columns like "date, description, amount"
3. **USE ACTUAL HEADERS**: If the document has column headers in the first row, use those EXACT names
4. **GENERIC NAMES**: If no clear headers, use: "Column 1", "Column 2", "Column 3", etc.
5. **EXTRACT EVERYTHING**: Every visible data row must be included
6. **PRESERVE STRUCTURE**: Keep column order as it appears in the document

RETURN FORMAT:
{
  "document_type": "bank_statement|invoice|receipt|table|spreadsheet|other",
  "columns": ["Column Name 1", "Column Name 2", "Column Name 3", ...],
  "rows": [
    {"Column Name 1": "value", "Column Name 2": "value", ...},
    {"Column Name 1": "value", "Column Name 2": "value", ...}
  ]
}

EXAMPLES:

Example 1 - Bank Statement with headers:
Document has headers: "Date | Description | Debit | Credit | Balance"
Return:
{
  "document_type": "bank_statement",
  "columns": ["Date", "Description", "Debit", "Credit", "Balance"],
  "rows": [
    {"Date": "2024-01-15", "Description": "ATM Withdrawal", "Debit": "500", "Credit": "", "Balance": "12500"},
    ...
  ]
}

Example 2 - Invoice WITHOUT clear headers:
Document is a messy invoice with: Item descriptions in column 1, quantities in column 2, prices in column 3
Return:
{
  "document_type": "invoice",
  "columns": ["Column 1", "Column 2", "Column 3"],
  "rows": [
    {"Column 1": "Widget A", "Column 2": "10", "Column 3": "199.99"},
    ...
  ]
}

Example 3 - Table with headers:
Document has: "Product Name | SKU | Stock | Price"
Return:
{
  "document_type": "table",
  "columns": ["Product Name", "SKU", "Stock", "Price"],
  "rows": [
    {"Product Name": "Item 1", "SKU": "ABC123", "Stock": "50", "Price": "29.99"},
    ...
  ]
}

RETURN ONLY THE JSON. NO TEXT BEFORE OR AFTER. NO MARKDOWN CODE BLOCKS."""

RETRY_PROMPTS = [
    # Retry 1: Ultra-simple
    """Extract ALL data from this image into a table.

If the document has column headers, use those names.
If not, use: "Column 1", "Column 2", etc.

Return JSON:
{
  "columns": ["col1", "col2", ...],
  "rows": [{"col1": "val", "col2": "val"}, ...]
}

ONLY JSON. NO TEXT.""",

    # Retry 2: Minimal
    """Look at this document. Extract every row of data.
Return:
{"columns": [...], "rows": [{...}]}

Use column names from the document or "Column 1", "Column 2" if unclear.""",

    # Retry 3: Raw fallback
    """Read everything visible in this document.
Return every line of text as structured rows.
{"columns": ["Text"], "rows": [{"Text": "line 1"}, {"Text": "line 2"}]}""",
]

# ═══════════════════════════════════════════════════════
# STEP 2: IMAGE PREPROCESSING
# ═══════════════════════════════════════════════════════

def preprocess_image(image_path):
    """Enhance image for better AI extraction."""
    try:
        from PIL import Image as PILImage, ImageEnhance
        img = PILImage.open(image_path)

        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        # Upscale if too small
        w, h = img.size
        if w < 1500:
            scale = 1500 / w
            img = img.resize((int(w * scale), int(h * scale)), PILImage.LANCZOS)

        # Enhance
        img = ImageEnhance.Contrast(img).enhance(1.4)
        img = ImageEnhance.Sharpness(img).enhance(1.8)
        img = ImageEnhance.Brightness(img).enhance(1.1)

        enhanced_path = image_path + '_enhanced.png'
        img.save(enhanced_path, 'PNG', quality=95)
        log_step('preprocess', f'Image enhanced: {w}x{h} → {img.size[0]}x{img.size[1]}')
        return enhanced_path
    except Exception as e:
        log_step('preprocess', f'Preprocessing failed (non-fatal): {e}')
        return image_path

# ═══════════════════════════════════════════════════════
# STEP 3: AI EXTRACTION (DYNAMIC)
# ═══════════════════════════════════════════════════════

async def ai_extract_dynamic(file_path, is_image, user_requirements='', attempt=0):
    """Universal AI extraction with dynamic column detection."""
    try:
        if is_image:
            enhanced_path = preprocess_image(file_path)
            with open(enhanced_path, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')
            
            prompt = UNIVERSAL_PROMPT if attempt == 0 else RETRY_PROMPTS[min(attempt - 1, len(RETRY_PROMPTS) - 1)]
            
            if user_requirements and user_requirements.strip():
                prompt += f"\n\nUSER REQUIREMENTS: {user_requirements}\nAdjust extraction based on these requirements."

            messages = [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all data from this document. Return ONLY JSON."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]
                }
            ]
        else:
            # Text-based extraction
            prompt = UNIVERSAL_PROMPT if attempt == 0 else RETRY_PROMPTS[min(attempt - 1, len(RETRY_PROMPTS) - 1)]
            
            if user_requirements and user_requirements.strip():
                prompt += f"\n\nUSER REQUIREMENTS: {user_requirements}"

            # For text, file_path is actually the text content
            text_content = str(file_path)[:12000]
            
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Extract all data from this text. Return ONLY JSON.\n\n{text_content}"}
            ]

        log_step('ai_extract', f'Calling GPT-4o (attempt {attempt + 1})')
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=4000,
            temperature=0
        )
        
        result = safe_parse_json(response.choices[0].message.content)
        if result:
            row_count = len(result.get('rows', []))
            col_count = len(result.get('columns', []))
            log_step('ai_extract', f'AI returned {col_count} columns, {row_count} rows')
        return result
    except Exception as e:
        log_step('ai_extract', f'AI extraction failed: {e}')
        return None

# ═══════════════════════════════════════════════════════
# STEP 4: JSON PARSING
# ═══════════════════════════════════════════════════════

def safe_parse_json(response):
    """Defensive JSON parsing."""
    if not response:
        return None
    text = response.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find outermost JSON
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    # Fix trailing commas
    try:
        fixed = re.sub(r',\s*([}\]])', r'\1', text)
        return json.loads(fixed)
    except (json.JSONDecodeError, Exception):
        pass

    log_step('json_parse', f'Failed to parse JSON: {text[:200]}')
    return None

# ═══════════════════════════════════════════════════════
# STEP 5: VALIDATION & NORMALIZATION
# ═══════════════════════════════════════════════════════

def validate_and_normalize(result):
    """Validate dynamic column result and clean data."""
    if not result or not isinstance(result, dict):
        return None

    columns = result.get('columns', [])
    rows = result.get('rows', [])

    if not columns or not rows:
        log_step('validate', 'Missing columns or rows')
        return None

    # Ensure all columns are strings
    columns = [str(col).strip() for col in columns if col]

    # Validate and clean rows
    validated_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue

        # Ensure row has all columns (fill missing with '')
        clean_row = {}
        for col in columns:
            value = row.get(col, '')
            clean_row[col] = str(value).strip() if value is not None else ''

        # Skip empty rows
        if all(not v for v in clean_row.values()):
            continue

        validated_rows.append(clean_row)

    if not validated_rows:
        log_step('validate', 'No valid rows after validation')
        return None

    result['columns'] = columns
    result['rows'] = validated_rows
    log_step('validate', f'Validated: {len(columns)} columns, {len(validated_rows)} rows')
    return result

# ═══════════════════════════════════════════════════════
# STEP 6: RETRY PIPELINE (NEVER FAIL)
# ═══════════════════════════════════════════════════════

async def extract_with_retry(file_path, is_image, user_requirements='', max_attempts=3):
    """Multi-attempt extraction with progressive fallback."""
    for attempt in range(max_attempts):
        result = await ai_extract_dynamic(file_path, is_image, user_requirements, attempt)
        
        if result:
            validated = validate_and_normalize(result)
            if validated:
                return validated
        
        log_step('retry', f'Attempt {attempt + 1}/{max_attempts} failed, retrying...')
    
    # NEVER FAIL: Return minimal fallback
    log_step('fallback', 'All attempts failed, creating minimal result')
    return {
        'document_type': 'other',
        'columns': ['Column 1'],
        'rows': [{'Column 1': 'Document uploaded but extraction incomplete. Please try again or contact support.'}]
    }

# ═══════════════════════════════════════════════════════
# STEP 7: FILE TYPE HANDLERS
# ═══════════════════════════════════════════════════════

def extract_text_from_pdf(file_path):
    """Extract text from PDF using pdfplumber."""
    try:
        import pdfplumber
        text = ''
        page_count = 0
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
        log_step('pdf', f'Extracted {len(text)} chars from {page_count} pages')
        is_scanned = len(text.strip()) < 80
        return text, is_scanned, page_count
    except Exception as e:
        log_step('pdf', f'PDF extraction failed: {e}')
        return '', True, 0

async def handle_image(file_path, user_requirements):
    """Process image file."""
    return await extract_with_retry(file_path, is_image=True, user_requirements=user_requirements)

async def handle_pdf(file_path, user_requirements):
    """Process PDF file."""
    text, is_scanned, page_count = extract_text_from_pdf(file_path)

    if is_scanned or len(text.strip()) < 80:
        log_step('pdf', 'Scanned PDF - converting to images')
        try:
            import pdfplumber
            all_results = []

            with pdfplumber.open(file_path) as pdf:
                pages_to_process = min(len(pdf.pages), 6)
                
                for i in range(pages_to_process):
                    try:
                        img = pdf.pages[i].to_image(resolution=220)
                        tmp_path = f'{file_path}_page{i}.png'
                        img.original.save(tmp_path, format='PNG')
                        
                        page_result = await extract_with_retry(tmp_path, is_image=True, user_requirements=user_requirements)
                        
                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass
                        
                        if page_result and page_result.get('rows'):
                            all_results.append(page_result)
                    except Exception as e:
                        log_step('pdf', f'Page {i} error: {e}')

            if not all_results:
                return await extract_with_retry(file_path, is_image=False, user_requirements=user_requirements)

            # Merge results from all pages
            merged_columns = all_results[0].get('columns', [])
            merged_rows = []
            for result in all_results:
                merged_rows.extend(result.get('rows', []))

            merged_result = {
                'document_type': all_results[0].get('document_type', 'other'),
                'columns': merged_columns,
                'rows': merged_rows
            }

            if page_count > 6:
                merged_result['page_warning'] = (
                    f"Only the first 6 of {page_count} pages were processed. "
                    "To extract all data, split your PDF into parts."
                )

            return validate_and_normalize(merged_result) or merged_result

        except Exception as e:
            log_step('pdf', f'PDF image processing failed: {e}')
            return await extract_with_retry(text, is_image=False, user_requirements=user_requirements)
    else:
        # Text PDF
        log_step('pdf', 'Text PDF - extracting from text')
        result = await extract_with_retry(text, is_image=False, user_requirements=user_requirements)
        
        if page_count > 6:
            result['page_warning'] = (
                f"Only the first 6 of {page_count} pages were processed."
            )
        
        return result

# ═══════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════

async def main():
    start_time = time.time()
    
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'No file path provided'}))
        sys.exit(1)

    file_path = sys.argv[1]
    user_requirements = sys.argv[2] if len(sys.argv) > 2 else ''

    if not os.path.exists(file_path):
        print(json.dumps({'error': f'File not found: {file_path}'}))
        sys.exit(1)

    ext = Path(file_path).suffix.lower()
    log_step('start', f'Processing {ext} file: {os.path.basename(file_path)}')
    if user_requirements:
        log_step('start', f'User requirements: {user_requirements[:200]}')

    try:
        if ext in ('.jpg', '.jpeg', '.png', '.webp'):
            result = await handle_image(file_path, user_requirements)
        elif ext == '.pdf':
            result = await handle_pdf(file_path, user_requirements)
        else:
            result = {
                'document_type': 'other',
                'columns': ['Error'],
                'rows': [{'Error': f'Unsupported file type: {ext}. Supported: PDF, JPG, PNG, WEBP'}]
            }

        # Add metadata
        elapsed = round(time.time() - start_time, 2)
        result['processing_time_seconds'] = elapsed
        result['pipeline_log'] = LOG_STEPS
        
        # Calculate summary stats
        rows = result.get('rows', [])
        result['summary'] = {
            'total_rows': len(rows),
            'total_columns': len(result.get('columns', [])),
        }

        log_step('done', f'Completed in {elapsed}s')
        print(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        log_step('fatal', f'Fatal error: {e}')
        # NEVER FAIL
        elapsed = round(time.time() - start_time, 2)
        fallback = {
            'document_type': 'other',
            'columns': ['Error'],
            'rows': [{'Error': 'Extraction encountered an error. Please try again.'}],
            'processing_time_seconds': elapsed,
            'partial': True
        }
        print(json.dumps(fallback, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(main())
