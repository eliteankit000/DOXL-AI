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
UNIVERSAL_PROMPT = """You are an expert data extraction AI specializing in creating CLEAN, STRUCTURED, EXCEL-LIKE spreadsheets.

TASK: Extract ALL data from this document into a HORIZONTAL TABLE FORMAT.

CRITICAL RULES:
1. **HORIZONTAL TABLES ONLY**: Convert ALL data into rows and columns (NOT vertical key-value lists)
2. **AUTO-DETECT STRUCTURE**: 
   - If document has a TABLE → preserve exact structure
   - If document has KEY-VALUE pairs → convert into SINGLE ROW with multiple columns
   - If document has REPEATED sections → create MULTIPLE ROWS
3. **CLEAN COLUMN NAMES**:
   - Remove special characters
   - Use Title Case
   - Keep names short and clear
   - Example: "Student's Name" → "Student Name"
   - Example: "Mobile No" → "Mobile"
4. **VALUE NORMALIZATION**:
   - Dates → DD/MM/YYYY format
   - Numbers → remove symbols, keep numeric
   - Text → trimmed, no extra spaces
5. **EXCEL-QUALITY OUTPUT**:
   - First row = headers
   - Next rows = data
   - No empty rows
   - No nested objects
   - Flat table structure

RETURN FORMAT:
{
  "document_type": "form|bank_statement|invoice|receipt|table|spreadsheet|other",
  "columns": ["Column Name 1", "Column Name 2", ...],
  "rows": [
    {"Column Name 1": "value1", "Column Name 2": "value2", ...}
  ]
}

EXAMPLES:

Example 1 - FORM with key-value pairs (CONVERT TO HORIZONTAL):
Document shows:
  Date: 03/04/2026
  Time: 13:38
  University: SAGE UNIVERSITY INDORE
  Form Type: Semester Registration Form

❌ WRONG (vertical):
{
  "columns": ["Field", "Value"],
  "rows": [
    {"Field": "Date", "Value": "03/04/2026"},
    {"Field": "Time", "Value": "13:38"}
  ]
}

✅ CORRECT (horizontal):
{
  "document_type": "form",
  "columns": ["Date", "Time", "University", "Form Type"],
  "rows": [
    {
      "Date": "03/04/2026",
      "Time": "13:38",
      "University": "SAGE UNIVERSITY INDORE",
      "Form Type": "Semester Registration Form"
    }
  ]
}

Example 2 - TABLE with headers (preserve structure):
Document has table: "Date | Description | Debit | Credit | Balance"
Return:
{
  "document_type": "bank_statement",
  "columns": ["Date", "Description", "Debit", "Credit", "Balance"],
  "rows": [
    {"Date": "15/01/2024", "Description": "ATM Withdrawal", "Debit": "500", "Credit": "", "Balance": "12500"},
    {"Date": "16/01/2024", "Description": "Salary Credit", "Debit": "", "Credit": "50000", "Balance": "62500"}
  ]
}

Example 3 - INVOICE (convert to horizontal):
Document shows invoice fields:
  Invoice #: INV-001
  Date: 15/03/2024
  Customer: John Doe
  Total: 5000

Return:
{
  "document_type": "invoice",
  "columns": ["Invoice Number", "Date", "Customer", "Total"],
  "rows": [
    {"Invoice Number": "INV-001", "Date": "15/03/2024", "Customer": "John Doe", "Total": "5000"}
  ]
}

Example 4 - MULTIPLE ITEMS (create multiple rows):
Document shows:
  Item 1: Widget A - Qty: 10 - Price: 100
  Item 2: Widget B - Qty: 5 - Price: 200

Return:
{
  "document_type": "invoice",
  "columns": ["Item", "Quantity", "Price"],
  "rows": [
    {"Item": "Widget A", "Quantity": "10", "Price": "100"},
    {"Item": "Widget B", "Quantity": "5", "Price": "200"}
  ]
}

IMPORTANT:
- ALWAYS convert key-value pairs into horizontal rows
- NEVER return vertical Field → Value format
- ALWAYS use clean, professional column names
- Output must be ready for Excel export

RETURN ONLY THE JSON. NO TEXT BEFORE OR AFTER. NO MARKDOWN CODE BLOCKS."""

RETRY_PROMPTS = [
    # Retry 1: Simplified horizontal format
    """Extract ALL data from this document into a HORIZONTAL TABLE (NOT vertical list).

RULES:
- If document has KEY-VALUE pairs → convert to SINGLE ROW
- If document has TABLE → preserve structure
- Clean column names (Title Case, no special chars)
- Return format: {"columns": [...], "rows": [{...}]}

Example:
Document: "Name: John, Age: 25, City: NYC"
Return: {"columns": ["Name", "Age", "City"], "rows": [{"Name": "John", "Age": "25", "City": "NYC"}]}

ONLY JSON. NO TEXT.""",

    # Retry 2: Ultra-minimal
    """Convert this document data into a spreadsheet table.
Return: {"columns": [...], "rows": [{...}]}

Make it horizontal (columns across top, values in rows below).""",

    # Retry 3: Fallback
    """Extract text and structure as table.
{"columns": ["Column 1", "Column 2"], "rows": [{"Column 1": "...", "Column 2": "..."}]}""",
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
# STEP 5: VERTICAL TO HORIZONTAL CONVERSION
# ═══════════════════════════════════════════════════════

def convert_vertical_to_horizontal(result):
    """
    Detect vertical key-value format and convert to horizontal table.
    
    Vertical format (WRONG):
    columns: ["Field", "Value"]
    rows: [
        {"Field": "Name", "Value": "John"},
        {"Field": "Age", "Value": "25"}
    ]
    
    Horizontal format (CORRECT):
    columns: ["Name", "Age"]
    rows: [{"Name": "John", "Age": "25"}]
    """
    if not result or not isinstance(result, dict):
        return result
    
    columns = result.get('columns', [])
    rows = result.get('rows', [])
    
    if not columns or not rows:
        return result
    
    # Detect vertical format: typically has 2 columns like ["Field", "Value"] or ["Key", "Value"]
    if len(columns) == 2:
        col1, col2 = columns[0].lower(), columns[1].lower()
        
        # Common vertical format indicators
        vertical_indicators = [
            ('field', 'value'),
            ('key', 'value'),
            ('name', 'value'),
            ('attribute', 'value'),
            ('property', 'value'),
            ('parameter', 'value'),
        ]
        
        is_vertical = any(
            (col1 == ind[0] or col1.startswith(ind[0])) and 
            (col2 == ind[1] or col2.startswith(ind[1]))
            for ind in vertical_indicators
        )
        
        if is_vertical:
            log_step('convert', f'Detected vertical format, converting to horizontal')
            
            # Extract new columns from first column values
            new_columns = []
            new_row = {}
            
            for row in rows:
                field_key = row.get(columns[0], '')
                field_value = row.get(columns[1], '')
                
                if field_key and isinstance(field_key, str):
                    # Clean column name
                    clean_key = clean_column_name(field_key)
                    new_columns.append(clean_key)
                    new_row[clean_key] = str(field_value).strip() if field_value else ''
            
            if new_columns:
                result['columns'] = new_columns
                result['rows'] = [new_row]
                log_step('convert', f'Converted to {len(new_columns)} columns, 1 row')
    
    return result

def clean_column_name(name):
    """Clean and normalize column names for Excel-quality output."""
    if not name or not isinstance(name, str):
        return 'Column'
    
    # Remove special characters except spaces and hyphens
    name = re.sub(r'[^\w\s-]', '', name)
    
    # Replace multiple spaces/hyphens with single space
    name = re.sub(r'[\s-]+', ' ', name)
    
    # Trim and title case
    name = name.strip().title()
    
    # Common replacements for cleaner names
    replacements = {
        'S Name': 'Name',
        'No ': 'Number ',
        'Id ': 'ID ',
        'Qty': 'Quantity',
        'Amt': 'Amount',
        'Desc': 'Description',
        'Tel': 'Telephone',
        'Mob': 'Mobile',
    }
    
    for old, new in replacements.items():
        name = name.replace(old, new)
    
    # Remove trailing spaces
    name = name.strip()
    
    return name if name else 'Column'

# ═══════════════════════════════════════════════════════
# STEP 6: VALIDATION & NORMALIZATION
# ═══════════════════════════════════════════════════════

def validate_and_normalize(result):
    """Validate dynamic column result and clean data."""
    if not result or not isinstance(result, dict):
        return None

    # STEP 1: Convert vertical to horizontal if needed
    result = convert_vertical_to_horizontal(result)

    columns = result.get('columns', [])
    rows = result.get('rows', [])

    if not columns or not rows:
        log_step('validate', 'Missing columns or rows')
        return None

    # STEP 2: Clean column names (Title Case, no special chars)
    cleaned_columns = [clean_column_name(col) for col in columns if col]
    
    if not cleaned_columns:
        log_step('validate', 'No valid columns after cleaning')
        return None

    # STEP 3: Create column mapping (old name → clean name)
    column_mapping = {}
    for i, old_col in enumerate(columns):
        if i < len(cleaned_columns):
            column_mapping[old_col] = cleaned_columns[i]

    # STEP 4: Validate and clean rows with new column names
    validated_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue

        # Map old column names to new clean names
        clean_row = {}
        for old_col, new_col in column_mapping.items():
            value = row.get(old_col, '')
            # Normalize value: trim whitespace, remove extra spaces
            clean_value = str(value).strip() if value is not None else ''
            clean_value = re.sub(r'\s+', ' ', clean_value)  # Replace multiple spaces with single
            clean_row[new_col] = clean_value

        # Skip empty rows
        if all(not v for v in clean_row.values()):
            continue

        validated_rows.append(clean_row)

    if not validated_rows:
        log_step('validate', 'No valid rows after validation')
        return None

    result['columns'] = cleaned_columns
    result['rows'] = validated_rows
    log_step('validate', f'Validated: {len(cleaned_columns)} columns, {len(validated_rows)} rows')
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
        # NEVER FAIL - return empty dataset
        elapsed = round(time.time() - start_time, 2)
        fallback = {
            'document_type': 'other',
            'columns': [],
            'rows': [],
            'processing_time_seconds': elapsed,
            'partial': True
        }
        print(json.dumps(fallback, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(main())
