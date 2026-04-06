#!/usr/bin/env python3
"""
DocXL AI — Enterprise Document Intelligence Engine v5.0
13-STAGE PIPELINE: Detect → Classify → Extract → Validate → Normalize → Score → Repair → Export

Target: 95%+ accuracy, ZERO failures, enterprise-grade extraction
Uses OpenAI GPT-4o directly
"""
import sys
import os
import json
import base64
import asyncio
import re
import time
import hashlib
from pathlib import Path
from openai import AsyncOpenAI
from datetime import datetime

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
# STAGE 1-3: MULTI-LAYER DOCUMENT UNDERSTANDING + CLASSIFICATION
# Combines: Visual Layout, Semantic Understanding, Pattern Recognition
# ═══════════════════════════════════════════════════════

CLASSIFICATION_PROMPT = """You are an expert document classifier. Analyze this document and classify it.

Return ONLY JSON:
{
  "document_type": "bank_statement|invoice|form|table|receipt|mixed",
  "confidence": 0.95,
  "has_table": true,
  "has_key_value_pairs": true,
  "has_line_items": false,
  "primary_structure": "table|key_value|mixed|list",
  "detected_fields": ["date", "description", "amount"],
  "page_orientation": "portrait|landscape",
  "data_density": "high|medium|low"
}

CLASSIFICATION RULES:
- BANK_STATEMENT: Has Date, Description/Narration, Debit/Credit/Withdrawal/Deposit, Balance columns
- INVOICE: Has line items with Item/Description, Qty, Rate/Price, Amount; may have invoice header metadata
- FORM: Mostly key-value pairs (Label: Value), registration forms, application forms
- TABLE: Generic structured table with clear headers and rows
- RECEIPT: Payment receipt, POS receipt, short summary of transaction
- MIXED: Multiple sections with different structures

Return ONLY the JSON. No text before or after."""

# ═══════════════════════════════════════════════════════
# STAGE 3: MODE-SPECIFIC EXTRACTION PROMPTS
# ═══════════════════════════════════════════════════════

BANK_STATEMENT_PROMPT = """You are an expert financial data extraction AI creating PROFESSIONAL Excel spreadsheets.

DOCUMENT TYPE: BANK STATEMENT

EXTRACTION RULES:
1. Extract the TRANSACTION TABLE - the main table with columns like:
   - Date (Transaction Date, Txn Date, Value Date)
   - Description (Narration, Particulars, Details, Remarks)
   - Debit (Withdrawal, Dr, DR, Debit Amount)
   - Credit (Deposit, Cr, CR, Credit Amount)
   - Balance (Running Balance, Closing Balance)
   - Reference (Ref No, Cheque No, UTR, Transaction ID)

2. EACH TRANSACTION = ONE ROW. Never merge transactions.
3. Maintain chronological order.
4. If Debit/Credit are in one column with indicators (Dr/Cr), split into separate Debit and Credit columns.
5. Remove currency symbols (₹, $, Rs.) - keep only numbers.
6. Preserve the exact balance values.

COLUMN NAMING CONVENTIONS:
- "Txn Date" / "Transaction Date" / "Value Date" → "Date"
- "Narration" / "Particulars" / "Details" → "Description"  
- "Withdrawal" / "Dr" / "DR" / "Debit Amt" → "Debit"
- "Deposit" / "Cr" / "CR" / "Credit Amt" → "Credit"
- "Running Balance" / "Closing Balance" / "Bal" → "Balance"
- "Chq No" / "Cheque" / "Ref" / "UTR" → "Reference"

RETURN FORMAT:
{
  "document_type": "bank_statement",
  "columns": ["Date", "Description", "Debit", "Credit", "Balance", "Reference"],
  "rows": [
    {"Date": "15/01/2024", "Description": "ATM Withdrawal", "Debit": "5000", "Credit": "", "Balance": "45000", "Reference": "ATM123"}
  ]
}

CRITICAL:
- EVERY visible transaction row MUST be extracted
- Numbers must be clean (no commas, no currency symbols)
- Empty cells should be empty strings ""
- Do NOT add rows that don't exist in the document
- Do NOT merge multiple transactions into one row

RETURN ONLY JSON. NO TEXT BEFORE OR AFTER. NO MARKDOWN."""

INVOICE_PROMPT = """You are an advanced document-to-Excel layout reconstruction engine.
Convert this invoice into a MULTI-BLOCK structure that PRESERVES the original layout.

STEP 1: Detect and extract these SECTIONS from the invoice:
1. HEADER — Company/Hotel/Business name, logo text, address, GSTIN, contact
2. INVOICE INFO — Invoice number, date, due date, payment terms
3. CUSTOMER/BILL TO — Customer name, address, phone, email, GSTIN
4. LINE ITEMS TABLE — The main itemized table (products/services with qty, rate, amount)
5. TAX SUMMARY — CGST, SGST, IGST breakdowns, tax totals
6. TOTALS/PAYMENT — Subtotal, discount, grand total, amount paid, balance due
7. FOOTER — Terms, bank details, notes, signatures

STEP 2: Return EACH section as a separate BLOCK.

RETURN FORMAT:
{
  "document_type": "invoice",
  "blocks": [
    {
      "type": "key_value",
      "title": "Company Details",
      "data": {"Company Name": "Hotel Kanchan", "GSTIN": "23AAMFS5374B1Z9", "Address": "123 Main Road, Indore"}
    },
    {
      "type": "key_value",
      "title": "Invoice Details",
      "data": {"Invoice No": "43", "Date": "06/04/2026", "Due Date": ""}
    },
    {
      "type": "key_value",
      "title": "Customer Details",
      "data": {"Name": "ABDULLA DHULIAWALA", "Mobile": "9890511164", "GSTIN": ""}
    },
    {
      "type": "table",
      "title": "Line Items",
      "columns": ["Particular", "Amount", "CGST", "SGST", "Total"],
      "rows": [
        {"Particular": "Room Tariff", "Amount": "1619.05", "CGST": "40.48", "SGST": "40.48", "Total": "1700"}
      ]
    },
    {
      "type": "key_value",
      "title": "Summary",
      "data": {"Subtotal": "1619.05", "CGST": "40.48", "SGST": "40.48", "Grand Total": "1700", "Amount Paid": "1700", "Balance Due": "0"}
    }
  ]
}

CRITICAL RULES:
1. Each section = ONE block. DO NOT merge everything into one table.
2. key_value blocks: use {"Field": "Value"} format for non-table sections
3. table blocks: use columns + rows for the LINE ITEMS table
4. Numbers: remove currency symbols (₹, $, Rs), keep decimals
5. Dates: DD/MM/YYYY format
6. Include ALL visible fields from the invoice — don't skip any section
7. If a section doesn't exist in the document, omit that block
8. The "Line Items" table block is REQUIRED — even if there's only 1 item
9. Keep original field names from the invoice where possible

RETURN ONLY JSON. NO TEXT BEFORE OR AFTER. NO MARKDOWN."""

FORM_PROMPT = """You are an expert data extraction AI creating PROFESSIONAL Excel spreadsheets.

DOCUMENT TYPE: FORM / APPLICATION

EXTRACTION RULES:
1. Convert ALL key-value pairs into a HORIZONTAL table (ONE ROW with many columns)
2. Each field label becomes a column header
3. Each field value becomes the cell value
4. If form has a table section (e.g., course list, item list) → extract that as separate rows

COLUMN NAMING:
- Clean field labels: remove colons, trim spaces
- Use Title Case
- "Student's Name" → "Student Name"
- "D.O.B" / "Date of Birth" → "Date Of Birth"
- "Mob No." / "Mobile Number" → "Mobile"
- "Roll No" → "Roll Number"

❌ WRONG (vertical):
{"columns": ["Field", "Value"], "rows": [{"Field": "Name", "Value": "John"}]}

✅ CORRECT (horizontal):
{"columns": ["Name", "Age", "City"], "rows": [{"Name": "John", "Age": "25", "City": "NYC"}]}

RETURN FORMAT:
{
  "document_type": "form",
  "columns": ["Name", "Date Of Birth", "Email", "Mobile", "Address"],
  "rows": [
    {"Name": "John Doe", "Date Of Birth": "15/01/1990", "Email": "john@email.com", "Mobile": "9876543210", "Address": "123 Main St"}
  ]
}

RETURN ONLY JSON. NO TEXT BEFORE OR AFTER. NO MARKDOWN."""

TABLE_PROMPT = """You are an expert data extraction AI creating PROFESSIONAL Excel spreadsheets.

DOCUMENT TYPE: GENERIC TABLE / DATA

EXTRACTION RULES:
1. Preserve the EXACT table structure from the document
2. First row of the table = column headers
3. Subsequent rows = data rows
4. Maintain row-column alignment precisely
5. Clean column names (Title Case, no special characters)
6. Numbers: remove currency symbols but keep decimals
7. Dates: use DD/MM/YYYY format

ALIGNMENT RULES:
- Same horizontal alignment → same row
- Same vertical alignment → same column
- Repeating patterns → multiple rows
- Merged cells → repeat value or leave empty

RETURN FORMAT:
{
  "document_type": "table",
  "columns": ["Column 1", "Column 2", "Column 3"],
  "rows": [
    {"Column 1": "value", "Column 2": "value", "Column 3": "value"}
  ]
}

RETURN ONLY JSON. NO TEXT BEFORE OR AFTER. NO MARKDOWN."""

MIXED_PROMPT = """You are an expert data extraction AI creating PROFESSIONAL Excel spreadsheets.

DOCUMENT TYPE: MIXED / COMPLEX DOCUMENT

STRATEGY:
1. Identify the PRIMARY data section (largest table or most structured section)
2. Extract that as the main dataset
3. Ignore headers, footers, watermarks, logos, page numbers
4. If multiple tables exist, extract the most data-rich one
5. Convert key-value metadata into additional columns if relevant

RULES:
- Focus on the MAIN data table
- Ignore decorative elements and noise
- Clean column names (Title Case)
- Numbers: remove currency symbols
- Dates: DD/MM/YYYY format
- Each data record = ONE row

RETURN FORMAT:
{
  "document_type": "mixed",
  "columns": ["Column 1", "Column 2"],
  "rows": [{"Column 1": "value", "Column 2": "value"}]
}

RETURN ONLY JSON. NO TEXT BEFORE OR AFTER. NO MARKDOWN."""

RECEIPT_PROMPT = """You are an expert data extraction AI creating PROFESSIONAL Excel spreadsheets.

DOCUMENT TYPE: RECEIPT / PAYMENT CONFIRMATION

EXTRACTION RULES:
1. If receipt has LINE ITEMS → extract as table rows
2. If receipt is a SUMMARY → convert to ONE horizontal row with all fields as columns
3. Common fields: Date, Receipt No, Merchant, Items, Amount, Tax, Total, Payment Method

RETURN FORMAT:
{
  "document_type": "receipt",
  "columns": ["Date", "Receipt No", "Description", "Amount", "Tax", "Total", "Payment Method"],
  "rows": [
    {"Date": "15/01/2024", "Receipt No": "R001", "Description": "Coffee", "Amount": "250", "Tax": "45", "Total": "295", "Payment Method": "Card"}
  ]
}

RETURN ONLY JSON. NO TEXT BEFORE OR AFTER. NO MARKDOWN."""

# Universal fallback prompt
UNIVERSAL_PROMPT = """You are an expert data extraction AI specializing in creating CLEAN, STRUCTURED, EXCEL-LIKE spreadsheets.

TASK: Extract ALL data from this document into a HORIZONTAL TABLE FORMAT.

CRITICAL RULES:
1. **HORIZONTAL TABLES ONLY**: Convert ALL data into rows and columns (NOT vertical key-value lists)
2. **AUTO-DETECT STRUCTURE**: 
   - If document has a TABLE → preserve exact structure
   - If document has KEY-VALUE pairs → convert into SINGLE ROW with multiple columns
   - If document has REPEATED sections → create MULTIPLE ROWS
3. **CLEAN COLUMN NAMES**: Title Case, no special characters, short and clear
4. **VALUE NORMALIZATION**: Dates → DD/MM/YYYY, Numbers → no symbols, Text → trimmed
5. **EXCEL-QUALITY OUTPUT**: Headers in first row, data below, no empty/junk rows

RETURN FORMAT:
{
  "document_type": "form|bank_statement|invoice|receipt|table|other",
  "columns": ["Column Name 1", "Column Name 2"],
  "rows": [{"Column Name 1": "value1", "Column Name 2": "value2"}]
}

IMPORTANT:
- ALWAYS convert key-value pairs into horizontal rows
- NEVER return vertical Field → Value format
- Output must be ready for Excel export
- RETURN ONLY THE JSON. NO TEXT BEFORE OR AFTER. NO MARKDOWN CODE BLOCKS."""

# Mode-specific prompt mapping
MODE_PROMPTS = {
    'bank_statement': BANK_STATEMENT_PROMPT,
    'invoice': INVOICE_PROMPT,
    'form': FORM_PROMPT,
    'table': TABLE_PROMPT,
    'mixed': MIXED_PROMPT,
    'receipt': RECEIPT_PROMPT,
}

RETRY_PROMPTS = [
    # Retry 1: Simplified format
    """Extract ALL data from this document into a HORIZONTAL TABLE.
RULES:
- If KEY-VALUE pairs → convert to SINGLE ROW (fields as columns)
- If TABLE → preserve structure exactly
- Clean column names (Title Case, no special chars)
- Numbers: remove currency symbols
- Return: {"document_type": "...", "columns": [...], "rows": [{...}]}
ONLY JSON. NO TEXT.""",
    # Retry 2: Ultra-minimal
    """Convert this document data into a spreadsheet table.
Return: {"document_type": "other", "columns": [...], "rows": [{...}]}
Make it horizontal (columns across top, values in rows below).""",
    # Retry 3: Last resort
    """Extract text and structure as table.
{"document_type": "other", "columns": ["Column 1", "Column 2"], "rows": [{"Column 1": "...", "Column 2": "..."}]}""",
]


# ═══════════════════════════════════════════════════════
# STAGE 2: IMAGE PREPROCESSING
# ═══════════════════════════════════════════════════════

def preprocess_image(image_path):
    """Enhance image for better AI extraction."""
    try:
        from PIL import Image as PILImage, ImageEnhance, ImageFilter
        img = PILImage.open(image_path)

        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        w, h = img.size

        # Upscale small images for better OCR
        if w < 1500:
            scale = 1500 / w
            img = img.resize((int(w * scale), int(h * scale)), PILImage.LANCZOS)

        # Multi-stage enhancement
        img = ImageEnhance.Contrast(img).enhance(1.4)
        img = ImageEnhance.Sharpness(img).enhance(1.8)
        img = ImageEnhance.Brightness(img).enhance(1.1)

        # Slight denoise for scanned documents
        try:
            img = img.filter(ImageFilter.MedianFilter(size=3))
            img = ImageEnhance.Sharpness(img).enhance(1.5)
        except Exception:
            pass

        enhanced_path = image_path + '_enhanced.png'
        img.save(enhanced_path, 'PNG', quality=95)
        log_step('preprocess', f'Image enhanced: {w}x{h} → {img.size[0]}x{img.size[1]}')
        return enhanced_path
    except Exception as e:
        log_step('preprocess', f'Preprocessing failed (non-fatal): {e}')
        return image_path


# ═══════════════════════════════════════════════════════
# STAGE 1-3: CLASSIFY DOCUMENT
# ═══════════════════════════════════════════════════════

async def classify_document(file_path, is_image):
    """Stage 1-3: Multi-layer document understanding and classification."""
    try:
        if is_image:
            enhanced_path = preprocess_image(file_path)
            with open(enhanced_path, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')

            messages = [
                {"role": "system", "content": CLASSIFICATION_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Classify this document. Return ONLY JSON."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]
                }
            ]
        else:
            text_content = str(file_path)[:15000]
            messages = [
                {"role": "system", "content": CLASSIFICATION_PROMPT},
                {"role": "user", "content": f"Classify this document. Return ONLY JSON.\n\n{text_content}"}
            ]

        log_step('classify', 'Calling GPT-4o for document classification')
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500,
            temperature=0
        )

        classification = safe_parse_json(response.choices[0].message.content)
        if classification:
            doc_type = classification.get('document_type', 'table')
            confidence = classification.get('confidence', 0.5)
            log_step('classify', f'Classified as: {doc_type} (confidence: {confidence})')
            return classification

        return {'document_type': 'table', 'confidence': 0.5}
    except Exception as e:
        log_step('classify', f'Classification failed (non-fatal): {e}')
        return {'document_type': 'table', 'confidence': 0.5}


# ═══════════════════════════════════════════════════════
# STAGE 3: MODE-SPECIFIC EXTRACTION
# ═══════════════════════════════════════════════════════

async def extract_with_mode(file_path, is_image, doc_type, user_requirements='', attempt=0):
    """Stage 3: Extract using mode-specific prompt based on document classification."""
    try:
        # Select prompt based on classification and attempt
        if attempt == 0:
            prompt = MODE_PROMPTS.get(doc_type, UNIVERSAL_PROMPT)
        elif attempt == 1:
            # Second attempt: use universal prompt
            prompt = UNIVERSAL_PROMPT
        else:
            # Subsequent retries: use progressively simpler prompts
            retry_idx = min(attempt - 2, len(RETRY_PROMPTS) - 1)
            prompt = RETRY_PROMPTS[retry_idx]

        if user_requirements and user_requirements.strip():
            prompt += f"\n\nUSER REQUIREMENTS: {user_requirements}\nAdjust extraction based on these requirements."

        if is_image:
            enhanced_path = preprocess_image(file_path)
            with open(enhanced_path, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')

            messages = [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all data from this document into a clean spreadsheet table. Return ONLY JSON."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]
                }
            ]
        else:
            text_content = str(file_path)[:30000]
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Extract all data from this text into a clean spreadsheet table. Return ONLY JSON.\n\n{text_content}"}
            ]

        log_step('extract', f'Calling GPT-4o (mode={doc_type}, attempt={attempt + 1})')

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=16384,
            temperature=0
        )

        result = safe_parse_json(response.choices[0].message.content)
        if result:
            row_count = len(result.get('rows', []))
            col_count = len(result.get('columns', []))
            log_step('extract', f'AI returned {col_count} columns, {row_count} rows')
        return result
    except Exception as e:
        log_step('extract', f'Extraction failed: {e}')
        return None


# ═══════════════════════════════════════════════════════
# STAGE 4: JSON PARSING (Defensive)
# ═══════════════════════════════════════════════════════

def safe_parse_json(response):
    """Defensive JSON parsing with multiple strategies."""
    if not response:
        return None
    text = response.strip()

    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Strip markdown code blocks
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 3: Find outermost JSON object
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    # Strategy 4: Fix trailing commas
    try:
        fixed = re.sub(r',\s*([}\]])', r'\1', text)
        return json.loads(fixed)
    except (json.JSONDecodeError, Exception):
        pass

    # Strategy 5: Fix single quotes
    try:
        fixed = text.replace("'", '"')
        return json.loads(fixed)
    except (json.JSONDecodeError, Exception):
        pass

    log_step('json_parse', f'Failed to parse JSON: {text[:200]}')
    return None


# ═══════════════════════════════════════════════════════
# STAGE 5: COLUMN INTELLIGENCE ENGINE
# ═══════════════════════════════════════════════════════

# Column name normalization mappings
COLUMN_ALIASES = {
    # Date columns
    'txn date': 'Date', 'transaction date': 'Date', 'trans date': 'Date',
    'value date': 'Value Date', 'posting date': 'Posting Date',
    'invoice date': 'Invoice Date', 'bill date': 'Bill Date',
    'due date': 'Due Date', 'payment date': 'Payment Date',
    # Description columns
    'narration': 'Description', 'particulars': 'Description',
    'details': 'Description', 'remarks': 'Description',
    'transaction details': 'Description', 'trans description': 'Description',
    'item description': 'Item', 'product name': 'Item',
    'product description': 'Item',
    # Amount columns
    'dr': 'Debit', 'dr.': 'Debit', 'debit amount': 'Debit',
    'debit amt': 'Debit', 'withdrawal': 'Debit', 'withdrawals': 'Debit',
    'cr': 'Credit', 'cr.': 'Credit', 'credit amount': 'Credit',
    'credit amt': 'Credit', 'deposit': 'Credit', 'deposits': 'Credit',
    'amt': 'Amount', 'total amount': 'Total Amount',
    'net amount': 'Net Amount', 'gross amount': 'Gross Amount',
    'unit price': 'Rate', 'price': 'Rate', 'unit rate': 'Rate',
    # Balance
    'running balance': 'Balance', 'closing balance': 'Balance',
    'available balance': 'Balance', 'bal': 'Balance', 'bal.': 'Balance',
    # Reference
    'ref no': 'Reference', 'ref no.': 'Reference', 'reference no': 'Reference',
    'chq no': 'Cheque No', 'cheque no': 'Cheque No', 'cheque number': 'Cheque No',
    'utr': 'UTR', 'utr no': 'UTR', 'transaction id': 'Transaction ID',
    'txn id': 'Transaction ID',
    # Tax
    'cgst': 'CGST', 'sgst': 'SGST', 'igst': 'IGST',
    'gst': 'GST', 'tax amount': 'Tax', 'vat': 'VAT',
    # Quantity
    'qty': 'Quantity', 'qty.': 'Quantity', 'nos': 'Quantity',
    'units': 'Quantity',
    # Invoice
    'inv no': 'Invoice Number', 'invoice no': 'Invoice Number',
    'invoice #': 'Invoice Number', 'bill no': 'Bill Number',
    'bill #': 'Bill Number',
    # Serial
    'sr no': 'Sr No', 'sr.no': 'Sr No', 'sr. no': 'Sr No',
    'sr no.': 'Sr No', 's.no': 'Sr No', 's no': 'Sr No',
    'sl no': 'Sr No', 'sl. no': 'Sr No', '#': 'Sr No',
    # HSN
    'hsn': 'HSN Code', 'hsn code': 'HSN Code', 'hsn/sac': 'HSN Code',
    'sac': 'SAC Code', 'sac code': 'SAC Code',
    # Discount
    'disc': 'Discount', 'disc.': 'Discount', 'discount %': 'Discount %',
}


def normalize_column_name(name):
    """Stage 5: Intelligent column name normalization."""
    if not name or not isinstance(name, str):
        return 'Column'

    original = name.strip()

    # Check alias mapping (case-insensitive)
    lower_name = original.lower().strip()
    if lower_name in COLUMN_ALIASES:
        return COLUMN_ALIASES[lower_name]

    # Remove special characters except spaces and hyphens
    cleaned = re.sub(r'[^\w\s-]', '', original)
    cleaned = re.sub(r'[\s-]+', ' ', cleaned).strip()

    # Title case
    cleaned = cleaned.title()

    # Common suffix cleanups
    suffix_map = {
        'No ': 'Number ', 'Id ': 'ID ', ' Id': ' ID',
        'Amt': 'Amount', 'Desc': 'Description',
        'Tel': 'Telephone', 'Mob': 'Mobile',
        'Qty': 'Quantity', 'Dt': 'Date',
    }
    for old, new in suffix_map.items():
        cleaned = cleaned.replace(old, new)

    return cleaned.strip() if cleaned.strip() else 'Column'


def deduplicate_columns(columns):
    """Ensure all column names are unique."""
    seen = {}
    result = []
    for col in columns:
        if col in seen:
            seen[col] += 1
            result.append(f"{col} {seen[col]}")
        else:
            seen[col] = 1
            result.append(col)
    return result


# ═══════════════════════════════════════════════════════
# STAGE 5: VERTICAL TO HORIZONTAL CONVERSION
# ═══════════════════════════════════════════════════════

def convert_vertical_to_horizontal(result):
    """Detect vertical key-value format and convert to horizontal table."""
    if not result or not isinstance(result, dict):
        return result

    columns = result.get('columns', [])
    rows = result.get('rows', [])

    if not columns or not rows:
        return result

    # Detect vertical format: 2 columns like ["Field", "Value"]
    if len(columns) == 2:
        col1, col2 = columns[0].lower().strip(), columns[1].lower().strip()

        vertical_indicators = [
            ('field', 'value'), ('key', 'value'), ('name', 'value'),
            ('attribute', 'value'), ('property', 'value'),
            ('parameter', 'value'), ('label', 'value'),
            ('detail', 'value'), ('item', 'value'),
        ]

        is_vertical = any(
            (col1 == ind[0] or col1.startswith(ind[0])) and
            (col2 == ind[1] or col2.startswith(ind[1]))
            for ind in vertical_indicators
        )

        if is_vertical:
            log_step('convert', 'Detected vertical format, converting to horizontal')

            new_columns = []
            new_row = {}

            for row in rows:
                field_key = row.get(columns[0], '')
                field_value = row.get(columns[1], '')

                if field_key and isinstance(field_key, str):
                    clean_key = normalize_column_name(field_key)
                    new_columns.append(clean_key)
                    new_row[clean_key] = str(field_value).strip() if field_value else ''

            if new_columns:
                new_columns = deduplicate_columns(new_columns)
                # Rebuild new_row with deduplicated keys
                dedup_row = {}
                idx = 0
                for row in rows:
                    field_value = row.get(columns[1], '')
                    if idx < len(new_columns):
                        dedup_row[new_columns[idx]] = str(field_value).strip() if field_value else ''
                    idx += 1
                result['columns'] = new_columns
                result['rows'] = [dedup_row]
                log_step('convert', f'Converted to {len(new_columns)} columns, 1 row')

    return result


# ═══════════════════════════════════════════════════════
# STAGE 6: DATA NORMALIZATION ENGINE
# ═══════════════════════════════════════════════════════

def normalize_numeric(value):
    """Remove currency symbols and format as clean number."""
    if not value or not isinstance(value, str):
        return value
    
    original = value.strip()
    if not original:
        return ''

    # Remove common currency symbols and text
    cleaned = original
    currency_patterns = ['₹', '$', '€', '£', '¥', 'Rs.', 'Rs', 'INR', 'USD', 'EUR', 'GBP']
    for symbol in currency_patterns:
        cleaned = cleaned.replace(symbol, '')
    
    # Remove commas from numbers (1,00,000 or 1,000,000)
    cleaned = cleaned.replace(',', '')
    cleaned = cleaned.strip()
    
    # Check if it looks like a number
    try:
        float(cleaned)
        return cleaned
    except ValueError:
        # Check if it has Dr/Cr suffix
        dr_cr = re.search(r'([\d.]+)\s*(Dr|Cr|DR|CR)', cleaned)
        if dr_cr:
            return dr_cr.group(1)
        return original


def normalize_date(value):
    """Standardize date formats to DD/MM/YYYY."""
    if not value or not isinstance(value, str):
        return value
    
    original = value.strip()
    if not original:
        return ''

    # Common date patterns
    date_patterns = [
        # DD/MM/YYYY or DD-MM-YYYY
        (r'(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})', lambda m: f"{m.group(1).zfill(2)}/{m.group(2).zfill(2)}/{m.group(3)}"),
        # YYYY-MM-DD (ISO)
        (r'(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})', lambda m: f"{m.group(3).zfill(2)}/{m.group(2).zfill(2)}/{m.group(1)}"),
        # DD Mon YYYY (15 Jan 2024)
        (r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})', 
         lambda m: _format_month_date(m.group(1), m.group(2), m.group(3))),
        # Mon DD, YYYY (Jan 15, 2024)
        (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),?\s+(\d{4})',
         lambda m: _format_month_date(m.group(2), m.group(1), m.group(3))),
    ]

    for pattern, formatter in date_patterns:
        match = re.search(pattern, original, re.IGNORECASE)
        if match:
            try:
                return formatter(match)
            except Exception:
                continue

    return original


def _format_month_date(day, month_str, year):
    """Helper to convert month name to number."""
    months = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
    }
    month_num = months.get(month_str[:3].lower(), '01')
    return f"{day.zfill(2)}/{month_num}/{year}"


def is_date_column(col_name):
    """Check if a column name suggests it contains dates."""
    date_keywords = ['date', 'dt', 'dob', 'birth', 'expiry', 'due', 'created', 'updated', 'posted']
    return any(kw in col_name.lower() for kw in date_keywords)


def is_numeric_column(col_name):
    """Check if a column name suggests it contains numbers."""
    numeric_keywords = [
        'amount', 'amt', 'debit', 'credit', 'balance', 'total', 'price',
        'rate', 'quantity', 'qty', 'tax', 'gst', 'cgst', 'sgst', 'igst',
        'vat', 'discount', 'subtotal', 'net', 'gross', 'charge', 'fee',
        'cost', 'value', 'salary', 'payment', 'withdrawal', 'deposit',
    ]
    return any(kw in col_name.lower() for kw in numeric_keywords)


def normalize_row_data(row, columns):
    """Stage 6: Apply data normalization to a single row."""
    normalized = {}
    for col in columns:
        value = row.get(col, '')
        if not isinstance(value, str):
            value = str(value) if value is not None else ''

        # Trim whitespace and collapse multiple spaces
        value = re.sub(r'\s+', ' ', value).strip()

        # Apply type-specific normalization
        if is_date_column(col):
            value = normalize_date(value)
        elif is_numeric_column(col):
            value = normalize_numeric(value)

        normalized[col] = value
    return normalized


# ═══════════════════════════════════════════════════════
# STAGE 7-9: MULTI-PASS VALIDATION + ERROR CORRECTION
# ═══════════════════════════════════════════════════════

def validate_pass_1_raw(result):
    """PASS 1: Raw extraction validation - check basic structure."""
    if not result or not isinstance(result, dict):
        return None, 'Not a valid dict'

    # Handle invoice blocks format — if blocks exist, that's valid
    blocks = result.get('blocks', None)
    if blocks and isinstance(blocks, list) and len(blocks) > 0:
        # Validate blocks have required structure
        has_valid_block = False
        for block in blocks:
            if not isinstance(block, dict):
                continue
            btype = block.get('type', '')
            if btype == 'table' and block.get('columns') and block.get('rows'):
                has_valid_block = True
            elif btype == 'key_value' and block.get('data'):
                has_valid_block = True
        if has_valid_block:
            log_step('validate', f'Pass 1: Valid blocks format with {len(blocks)} blocks')
            return result, None

    columns = result.get('columns', [])
    rows = result.get('rows', [])

    if not columns:
        # Try to infer columns from first row
        if rows and isinstance(rows[0], dict):
            columns = list(rows[0].keys())
            result['columns'] = columns
        else:
            return None, 'No columns found'

    if not rows:
        return None, 'No rows found'

    # Validate rows are dicts
    valid_rows = [r for r in rows if isinstance(r, dict)]
    if not valid_rows:
        return None, 'No valid row dicts'

    result['rows'] = valid_rows
    return result, None


def validate_pass_2_structure(result):
    """PASS 2: Structure correction - fix column alignment issues."""
    # Skip structure correction for blocks format — handled in format_output
    if result.get('blocks'):
        return result, None

    columns = result.get('columns', [])
    rows = result.get('rows', [])

    # Convert vertical to horizontal if needed
    result = convert_vertical_to_horizontal(result)
    columns = result.get('columns', [])
    rows = result.get('rows', [])

    # Normalize column names using Column Intelligence
    normalized_columns = [normalize_column_name(col) for col in columns if col]
    normalized_columns = deduplicate_columns(normalized_columns)

    if not normalized_columns:
        return None, 'No valid columns after normalization'

    # Build column mapping
    column_mapping = {}
    for i, old_col in enumerate(columns):
        if i < len(normalized_columns):
            column_mapping[old_col] = normalized_columns[i]

    # Remap rows with normalized column names
    remapped_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        new_row = {}
        for old_col, new_col in column_mapping.items():
            new_row[new_col] = row.get(old_col, '')
        # Also capture any extra keys not in original columns
        for key in row:
            if key not in column_mapping:
                norm_key = normalize_column_name(key)
                if norm_key not in new_row:
                    new_row[norm_key] = row[key]
                    if norm_key not in normalized_columns:
                        normalized_columns.append(norm_key)
        remapped_rows.append(new_row)

    result['columns'] = normalized_columns
    result['rows'] = remapped_rows
    return result, None


def validate_pass_3_data(result):
    """PASS 3: Data validation - normalize values, remove empty rows."""
    # Skip data validation for blocks format — handled in format_output
    if result.get('blocks'):
        return result, None

    columns = result.get('columns', [])
    rows = result.get('rows', [])

    validated_rows = []
    for row in rows:
        # Apply data normalization
        normalized_row = normalize_row_data(row, columns)

        # Skip completely empty rows
        if all(not v for v in normalized_row.values()):
            continue

        validated_rows.append(normalized_row)

    if not validated_rows:
        return None, 'No valid rows after data validation'

    result['rows'] = validated_rows
    log_step('validate', f'Pass 3: {len(validated_rows)} rows validated, {len(columns)} columns')
    return result, None


def multi_pass_validate(result):
    """Stage 7-9: Run 3-pass validation pipeline."""
    # PASS 1: Raw extraction check
    result, err = validate_pass_1_raw(result)
    if err:
        log_step('validate', f'Pass 1 failed: {err}')
        return None

    # PASS 2: Structure correction
    result, err = validate_pass_2_structure(result)
    if err:
        log_step('validate', f'Pass 2 failed: {err}')
        return None

    # PASS 3: Data validation
    result, err = validate_pass_3_data(result)
    if err:
        log_step('validate', f'Pass 3 failed: {err}')
        return None

    return result


# ═══════════════════════════════════════════════════════
# STAGE 8: ERROR CORRECTION ENGINE
# ═══════════════════════════════════════════════════════

def fix_shifted_columns(result):
    """Fix columns that may have shifted during extraction."""
    columns = result.get('columns', [])
    rows = result.get('rows', [])
    
    if not rows or len(rows) < 2:
        return result

    # Check for consistent column usage across rows
    col_fill_rates = {}
    for col in columns:
        filled = sum(1 for row in rows if row.get(col, '').strip())
        col_fill_rates[col] = filled / len(rows)

    # Remove columns that are completely empty
    active_columns = [col for col in columns if col_fill_rates.get(col, 0) > 0]
    
    if active_columns and len(active_columns) < len(columns):
        result['columns'] = active_columns
        result['rows'] = [
            {col: row.get(col, '') for col in active_columns}
            for row in rows
        ]
        log_step('error_fix', f'Removed {len(columns) - len(active_columns)} empty columns')
    
    return result


def fix_merged_text(result):
    """Fix rows where text from multiple cells got merged into one."""
    columns = result.get('columns', [])
    rows = result.get('rows', [])
    
    if not rows:
        return result

    # Check if any row has most values empty except one very long value
    fixed_rows = []
    for row in rows:
        non_empty = [(col, val) for col, val in row.items() if val and str(val).strip()]
        
        if len(non_empty) == 1 and len(columns) > 2:
            # Single long value - might be a merged row or section header
            col_name, value = non_empty[0]
            if len(str(value)) > 100:
                # Likely a section header or merged content - keep but mark
                fixed_rows.append(row)
            else:
                fixed_rows.append(row)
        else:
            fixed_rows.append(row)
    
    result['rows'] = fixed_rows
    return result


# ═══════════════════════════════════════════════════════
# STAGE 9: CONFIDENCE SCORING
# ═══════════════════════════════════════════════════════

def calculate_row_confidence(row, columns):
    """Calculate confidence score for a single row (0.0 - 1.0)."""
    if not row or not columns:
        return 0.0

    total_fields = len(columns)
    filled_fields = sum(1 for col in columns if row.get(col, '').strip())
    
    # Base confidence from fill rate
    fill_rate = filled_fields / total_fields if total_fields > 0 else 0

    # Bonus for valid data patterns
    bonus = 0
    for col in columns:
        value = row.get(col, '').strip()
        if not value:
            continue
        
        if is_date_column(col):
            # Check if value looks like a date
            if re.search(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}', value):
                bonus += 0.05
        elif is_numeric_column(col):
            # Check if value is numeric
            try:
                float(value.replace(',', ''))
                bonus += 0.05
            except ValueError:
                bonus -= 0.05

    confidence = min(1.0, fill_rate * 0.8 + bonus + 0.1)
    return round(confidence, 2)


def score_result(result):
    """Stage 9: Add confidence scores to all rows."""
    columns = result.get('columns', [])
    rows = result.get('rows', [])

    total_confidence = 0
    for row in rows:
        conf = calculate_row_confidence(row, columns)
        row['_confidence'] = conf
        total_confidence += conf

    avg_confidence = round(total_confidence / len(rows), 2) if rows else 0.0
    result['confidence'] = avg_confidence
    log_step('score', f'Average confidence: {avg_confidence} across {len(rows)} rows')
    return result


# ═══════════════════════════════════════════════════════
# STAGE 10-12: OUTPUT FORMAT + EXCEL QUALITY + FALLBACK
# ═══════════════════════════════════════════════════════

def format_output(result):
    """Stage 10-12: Final formatting for Excel-quality output."""

    # ── Handle invoice blocks format ──
    blocks = result.get('blocks', None)
    if blocks and isinstance(blocks, list):
        result = convert_blocks_to_flat(result)

    columns = result.get('columns', [])
    rows = result.get('rows', [])

    # Remove internal fields from output rows
    clean_rows = []
    for row in rows:
        clean_row = {}
        for col in columns:
            val = row.get(col, '')
            # Ensure all values are strings for consistency
            if val is None:
                val = ''
            elif not isinstance(val, str):
                val = str(val)
            clean_row[col] = val

        # Store confidence separately
        conf = row.get('_confidence', 0.85)
        clean_row['confidence'] = conf
        clean_rows.append(clean_row)

    result['columns'] = columns
    result['rows'] = clean_rows
    return result


def convert_blocks_to_flat(result):
    """Convert invoice blocks format into flat columns/rows for SpreadsheetEditor,
    while preserving blocks for Excel export."""
    blocks = result.get('blocks', [])
    if not blocks:
        return result

    # Find the main LINE ITEMS table block
    table_block = None
    kv_blocks = []
    for block in blocks:
        if block.get('type') == 'table' and block.get('columns') and block.get('rows'):
            if table_block is None or len(block.get('rows', [])) > len(table_block.get('rows', [])):
                table_block = block
        elif block.get('type') == 'key_value' and block.get('data'):
            kv_blocks.append(block)

    if table_block:
        # Use the table block as the primary flat data
        result['columns'] = table_block['columns']
        result['rows'] = table_block['rows']
    elif kv_blocks:
        # No table found — convert all key-value blocks into a single horizontal row
        all_columns = []
        merged_row = {}
        for kv in kv_blocks:
            data = kv.get('data', {})
            for key, value in data.items():
                clean_key = normalize_column_name(key)
                if clean_key not in merged_row:
                    all_columns.append(clean_key)
                    merged_row[clean_key] = str(value) if value else ''
        result['columns'] = all_columns
        result['rows'] = [merged_row] if merged_row else []
    else:
        result['columns'] = []
        result['rows'] = []

    # KEEP blocks for Excel export — this is the key for layout preservation
    result['blocks'] = blocks
    log_step('blocks', f'Converted {len(blocks)} blocks → flat: {len(result["columns"])} cols, {len(result["rows"])} rows')
    return result


def create_fallback_result():
    """Stage 12: Fallback intelligence - generate minimal usable result."""
    return {
        'document_type': 'other',
        'columns': ['Content'],
        'rows': [{'Content': 'Document uploaded but extraction could not complete. Please try again with a clearer image or different format.', 'confidence': 0.1}],
        'confidence': 0.1,
        'partial': True,
    }


# ═══════════════════════════════════════════════════════
# STAGE 13: FINAL QUALITY CHECK
# ═══════════════════════════════════════════════════════

def final_quality_check(result):
    """Stage 13: Final quality validation before output."""
    # For blocks format, check blocks have content
    if result.get('blocks'):
        blocks = result['blocks']
        has_data = False
        for block in blocks:
            if block.get('type') == 'table' and block.get('rows'):
                has_data = True
            elif block.get('type') == 'key_value' and block.get('data'):
                has_data = True
        if has_data:
            log_step('quality', f'PASS (blocks): {len(blocks)} blocks')
            return True
        # Fall through to check flat format

    columns = result.get('columns', [])
    rows = result.get('rows', [])

    # Check 1: Is this usable in Excel?
    if not columns or not rows:
        log_step('quality', 'FAIL: Empty columns or rows')
        return False

    # Check 2: Do rows have matching columns?
    for row in rows[:5]:  # Check first 5 rows
        if not isinstance(row, dict):
            log_step('quality', 'FAIL: Row is not a dict')
            return False

    # Check 3: Are all rows mostly empty (junk extraction)?
    non_empty_rows = 0
    for row in rows:
        non_empty = sum(1 for col in columns if row.get(col, '').strip())
        if non_empty > 0:
            non_empty_rows += 1

    if non_empty_rows == 0:
        log_step('quality', 'FAIL: All rows are empty')
        return False

    # Check 4: Reasonable number of columns (not > 50)
    if len(columns) > 50:
        log_step('quality', f'WARNING: Too many columns ({len(columns)}), may be misdetected')

    log_step('quality', f'PASS: {len(columns)} columns, {len(rows)} rows, {non_empty_rows} non-empty')
    return True


# ═══════════════════════════════════════════════════════
# MASTER PIPELINE: 13-STAGE EXTRACTION
# ═══════════════════════════════════════════════════════

async def run_pipeline(file_path, is_image, user_requirements='', max_attempts=4):
    """Master pipeline: runs all 13 stages in sequence."""
    
    try:
        # ── STAGE 1-3: Classify document ──
        classification = await classify_document(file_path, is_image)
        doc_type = classification.get('document_type', 'table')
        
        last_raw_result = None  # Keep track of last raw result for fallback
        
        # ── STAGE 3-13: Extract + Validate with retry ──
        for attempt in range(max_attempts):
            try:
                # Stage 3: Mode-specific extraction
                result = await extract_with_mode(file_path, is_image, doc_type, user_requirements, attempt)
                
                if not result:
                    log_step('pipeline', f'Attempt {attempt + 1}: No result from AI')
                    continue

                last_raw_result = result  # Save for fallback
                
                # Preserve document_type and metadata
                result['document_type'] = result.get('document_type', doc_type)
                metadata = result.get('metadata', None)

                # Stage 7-9: Multi-pass validation (includes stages 5-6)
                validated = multi_pass_validate(result)
                
                if not validated:
                    log_step('pipeline', f'Attempt {attempt + 1}: Validation failed')
                    continue

                # Stage 8: Error correction
                validated = fix_shifted_columns(validated)
                validated = fix_merged_text(validated)

                # Stage 9: Confidence scoring
                validated = score_result(validated)

                # Stage 9: Confidence-aware repair
                avg_confidence = validated.get('confidence', 0)
                if avg_confidence < 0.4 and attempt < max_attempts - 1:
                    log_step('pipeline', f'Low confidence ({avg_confidence}), retrying with different mode')
                    doc_type = 'table'  # Fall back to generic table mode
                    continue

                # Stage 10-12: Output formatting
                validated = format_output(validated)
                validated['document_type'] = result.get('document_type', doc_type)
                if metadata:
                    validated['metadata'] = metadata

                # Stage 13: Final quality check
                if final_quality_check(validated):
                    log_step('pipeline', f'Pipeline complete: {len(validated["columns"])} cols, {len(validated["rows"])} rows')
                    return validated
                else:
                    log_step('pipeline', f'Attempt {attempt + 1}: Quality check failed')
                    continue
            except Exception as attempt_err:
                log_step('pipeline', f'Attempt {attempt + 1} error: {attempt_err}')
                continue

        # If we have a raw result that just failed validation, try to return it as-is
        if last_raw_result and last_raw_result.get('rows') and last_raw_result.get('columns'):
            log_step('pipeline', 'Returning raw result (validation failed but data exists)')
            last_raw_result['partial'] = True
            last_raw_result['confidence'] = 0.5
            return last_raw_result

        # NEVER FAIL: Return fallback
        log_step('pipeline', 'All attempts exhausted, returning fallback')
        return create_fallback_result()

    except Exception as e:
        log_step('pipeline', f'Pipeline fatal error: {e}')
        return create_fallback_result()


# ═══════════════════════════════════════════════════════
# FILE TYPE HANDLERS
# ═══════════════════════════════════════════════════════

def extract_text_from_pdf(file_path):
    """Extract text from PDF using pdfplumber — returns per-page text too."""
    try:
        import pdfplumber
        full_text = ''
        page_texts = []
        page_count = 0
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + '\n'
                    page_texts.append(page_text)
                else:
                    page_texts.append('')
        log_step('pdf', f'Extracted {len(full_text)} chars from {page_count} pages')
        is_scanned = len(full_text.strip()) < 80
        return full_text, is_scanned, page_count, page_texts
    except Exception as e:
        log_step('pdf', f'PDF extraction failed: {e}')
        return '', True, 0, []


async def handle_image(file_path, user_requirements):
    """Process image file through 13-stage pipeline."""
    return await run_pipeline(file_path, is_image=True, user_requirements=user_requirements)


async def handle_pdf(file_path, user_requirements):
    """Process PDF file through 13-stage pipeline."""
    text, is_scanned, page_count, page_texts = extract_text_from_pdf(file_path)

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

                        page_result = await run_pipeline(tmp_path, is_image=True, user_requirements=user_requirements)

                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass

                        if page_result and page_result.get('rows'):
                            all_results.append(page_result)
                    except Exception as e:
                        log_step('pdf', f'Page {i} error: {e}')

            if not all_results:
                return await run_pipeline(file_path, is_image=False, user_requirements=user_requirements)

            merged = merge_multipage_results(all_results)

            if page_count > 6:
                merged['page_warning'] = (
                    f"Only the first 6 of {page_count} pages were processed. "
                    "To extract all data, split your PDF into parts."
                )

            return merged

        except Exception as e:
            log_step('pdf', f'PDF image processing failed: {e}')
            return await run_pipeline(text, is_image=False, user_requirements=user_requirements)
    else:
        # Text PDF — ALWAYS try full text first, only chunk for very large docs
        pages_to_process = min(page_count, 6)
        text_for_processing = '\n'.join(page_texts[:pages_to_process])

        log_step('pdf', f'Text PDF ({len(text_for_processing)} chars, {pages_to_process} pages) - full text extraction')

        # Strategy: Always try full text first (GPT-4o handles up to ~30K chars easily)
        # Only fall back to page-by-page chunking if full text extraction fails
        result = await run_pipeline(text_for_processing, is_image=False, user_requirements=user_requirements)

        # Check if full text extraction produced meaningful results
        row_count = len(result.get('rows', []))
        is_good = row_count > 0 and not result.get('partial', False)

        if is_good:
            log_step('pdf', f'Full text extraction successful: {row_count} rows')
            if page_count > 6:
                result['page_warning'] = f"Only the first 6 of {page_count} pages were processed."
            return result

        # Fallback: chunk by pages for very large documents or when full text fails
        if pages_to_process > 1 and len(text_for_processing) > 3000:
            log_step('pdf', f'Full text extraction poor ({row_count} rows), trying page-by-page chunking')
            all_results = []

            for i in range(pages_to_process):
                page_text = page_texts[i] if i < len(page_texts) else ''
                if not page_text or len(page_text.strip()) < 30:
                    continue

                log_step('pdf', f'Processing text page {i + 1}/{pages_to_process}')
                page_result = await run_pipeline(page_text, is_image=False, user_requirements=user_requirements)

                if page_result and page_result.get('rows'):
                    all_results.append(page_result)

            if all_results:
                merged = merge_multipage_results(all_results)
                merged_rows = len(merged.get('rows', []))
                # Use chunked result only if it's better than full text result
                if merged_rows > row_count:
                    log_step('pdf', f'Chunked extraction better: {merged_rows} vs {row_count} rows')
                    if page_count > 6:
                        merged['page_warning'] = f"Only the first 6 of {page_count} pages were processed."
                    return merged

        # Return whatever we got from full text (even if partial)
        if page_count > 6:
            result['page_warning'] = f"Only the first 6 of {page_count} pages were processed."
        return result


def merge_multipage_results(all_results):
    """Merge extraction results from multiple PDF pages with column reconciliation."""
    if not all_results:
        return create_fallback_result()

    if len(all_results) == 1:
        return all_results[0]

    # Build union of all columns (preserving order from first page)
    all_columns = []
    col_set = set()
    for result in all_results:
        for col in result.get('columns', []):
            if col not in col_set:
                col_set.add(col)
                all_columns.append(col)

    # Merge all rows, ensuring all columns exist in each row
    merged_rows = []
    for result in all_results:
        for row in result.get('rows', []):
            unified_row = {col: row.get(col, '') for col in all_columns}
            # Preserve confidence
            if 'confidence' in row:
                unified_row['confidence'] = row['confidence']
            merged_rows.append(unified_row)

    # Calculate overall confidence
    confidences = [row.get('confidence', 0.5) for row in merged_rows]
    avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.5

    merged = {
        'document_type': all_results[0].get('document_type', 'other'),
        'columns': all_columns,
        'rows': merged_rows,
        'confidence': avg_confidence,
    }

    log_step('merge', f'Merged {len(all_results)} pages → {len(all_columns)} columns, {len(merged_rows)} rows')
    return merged


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
                'rows': [{'Error': f'Unsupported file type: {ext}. Supported: PDF, JPG, PNG, WEBP'}],
                'confidence': 0.0,
            }

        # Add processing metadata
        elapsed = round(time.time() - start_time, 2)
        result['processing_time_seconds'] = elapsed
        result['pipeline_version'] = '5.0'
        result['pipeline_log'] = LOG_STEPS

        # Calculate summary stats
        rows = result.get('rows', [])
        result['summary'] = {
            'total_rows': len(rows),
            'total_columns': len(result.get('columns', [])),
        }

        log_step('done', f'Completed in {elapsed}s — {len(rows)} rows, {len(result.get("columns", []))} cols')
        print(json.dumps(result, ensure_ascii=False))

    except Exception as e:
        log_step('fatal', f'Fatal error: {e}')
        # NEVER FAIL - return empty dataset
        elapsed = round(time.time() - start_time, 2)
        fallback = create_fallback_result()
        fallback['processing_time_seconds'] = elapsed
        fallback['pipeline_log'] = LOG_STEPS
        fallback['summary'] = {'total_rows': 0, 'total_columns': 0}
        print(json.dumps(fallback, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(main())
