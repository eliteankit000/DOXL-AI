#!/usr/bin/env python3
"""
DocXL AI — Production Extraction Engine v3.0
Architecture: Detect → Dual Extract → Validate → Normalize → Score → Retry(x3) → Instruct
Target: 90-95% accuracy, ZERO failures
Uses OpenAI GPT-4o directly
"""
import sys
import os
import json
import base64
import asyncio
import re
import io
import time
from pathlib import Path
from datetime import datetime
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
# STEP 1: FILE TYPE DETECTION
# ═══════════════════════════════════════════════════════

BANK_KEYWORDS = [
    'balance', 'debit', 'credit', 'transaction', 'account no', 'account number',
    'ifsc', 'branch', 'statement', 'closing balance', 'opening balance',
    'withdrawal', 'deposit', 'utr', 'neft', 'imps', 'rtgs', 'chq', 'cheque',
    'available balance', 'ledger', 'passbook', 'bank', 'savings', 'current account'
]

INVOICE_KEYWORDS = [
    'invoice', 'bill to', 'ship to', 'gst', 'cgst', 'sgst', 'igst', 'hsn',
    'invoice no', 'invoice number', 'tax invoice', 'proforma', 'quotation',
    'subtotal', 'grand total', 'due date', 'payment due', 'vendor', 'supplier',
    'qty', 'quantity', 'unit price', 'rate', 'amount', 'item', 'description',
    'total amount', 'invoice date', 'po number', 'purchase order'
]

RECEIPT_KEYWORDS = [
    'receipt', 'received from', 'payment received', 'thank you for your purchase',
    'order id', 'order number', 'cashier', 'store', 'shop', 'retail',
    'subtotal', 'discount', 'tax', 'total paid', 'change', 'cash', 'card'
]

def detect_document_type_from_text(text):
    """Keyword-based fast detection from extracted text."""
    text_lower = text.lower()
    bank_score = sum(1 for kw in BANK_KEYWORDS if kw in text_lower)
    invoice_score = sum(1 for kw in INVOICE_KEYWORDS if kw in text_lower)
    receipt_score = sum(1 for kw in RECEIPT_KEYWORDS if kw in text_lower)

    scores = {'bank_statement': bank_score, 'invoice': invoice_score, 'receipt': receipt_score}
    best = max(scores, key=scores.get)
    log_step('detect', f'Scores: bank={bank_score} invoice={invoice_score} receipt={receipt_score} → {best if scores[best] >= 2 else "table"}')
    if scores[best] >= 2:
        return best
    return 'table'

# ═══════════════════════════════════════════════════════
# STEP 2A: TEXT PDF PARSER (fast path — pdfplumber)
# ═══════════════════════════════════════════════════════

def extract_text_from_pdf(file_path):
    """Returns (text, is_scanned, page_count). is_scanned=True means text extraction failed."""
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
        log_step('ocr', f'Extracted {len(text)} chars from {page_count} pages')
        if len(text.strip()) > 80:
            return text, False, page_count
        return text, True, page_count
    except Exception as e:
        log_step('ocr', f'PDF text extraction failed: {e}')
        return '', True, 0

def parse_bank_statement_text(text):
    """Rule-based parser for bank statement text — handles common formats."""
    rows = []
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    date_pattern = re.compile(
        r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-]\d{2}[\/\-]\d{2}|\d{2}\s+\w{3}\s+\d{4})'
    )
    amount_pattern = re.compile(r'[\d,]+\.?\d{0,2}')

    for line in lines:
        date_match = date_pattern.search(line)
        if not date_match:
            continue

        amounts = amount_pattern.findall(line.replace(',', ''))
        amounts = [float(a) for a in amounts if a and float(a) > 0]
        if not amounts:
            continue

        date_str = date_match.group(0)
        after_date = line[date_match.end():].strip()

        tx_type = 'debit'
        line_lower = line.lower()
        if any(w in line_lower for w in ['cr', 'credit', 'deposit', 'received', '+']):
            tx_type = 'credit'
        if any(w in line_lower for w in ['dr', 'debit', 'withdrawal', 'paid', '-']):
            tx_type = 'debit'

        desc = re.sub(r'[\d,]+\.?\d*', '', after_date).strip()
        desc = re.sub(r'\s+', ' ', desc).strip(' /-')
        if not desc:
            desc = 'Transaction'

        amount = amounts[0] if amounts else 0
        balance = amounts[-1] if len(amounts) > 1 else 0

        rows.append({
            'date': normalize_date_str(date_str),
            'description': desc[:200],
            'amount': round(abs(amount), 2),
            'type': tx_type,
            'category': infer_category(desc),
            'gst': 0.0,
            'reference': '',
            'confidence': 0.75,
            '_balance': round(balance, 2),
        })

    log_step('rule_parse', f'Bank statement parser: {len(rows)} rows')
    return rows

def parse_invoice_text(text):
    """Rule-based parser for invoice text."""
    rows = []
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    invoice_date = ''
    date_pattern = re.compile(
        r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]?\d{2}[\/\-\.]?\d{2})'
    )
    for line in lines:
        if any(w in line.lower() for w in ['date', 'invoice date', 'bill date']):
            dm = date_pattern.search(line)
            if dm:
                invoice_date = normalize_date_str(dm.group(0))
                break

    amount_pattern = re.compile(r'[\d,]+\.?\d{0,2}')

    for line in lines:
        skip_words = ['total', 'subtotal', 'grand total', 'tax', 'cgst', 'sgst',
                      'igst', 'discount', 'balance due', 'amount due', 'hsn']
        if any(sw in line.lower() for sw in skip_words):
            continue

        amounts = amount_pattern.findall(line.replace(',', ''))
        amounts = [float(a) for a in amounts if float(a) > 0.5]
        if len(amounts) < 1:
            continue

        desc = re.sub(r'[\d,]+\.?\d*', '', line).strip()
        desc = re.sub(r'\s+', ' ', desc).strip(' /-|:')
        if len(desc) < 2:
            continue

        amount = amounts[-1] if amounts else 0
        gst_amount = 0.0
        if len(amounts) >= 2:
            potential_gst = amounts[-2]
            if 0 < potential_gst < amount * 0.30:
                gst_amount = potential_gst

        rows.append({
            'date': invoice_date,
            'description': desc[:200],
            'amount': round(abs(amount), 2),
            'type': 'expense',
            'category': infer_category(desc),
            'gst': round(gst_amount, 2),
            'reference': '',
            'confidence': 0.70,
        })

    log_step('rule_parse', f'Invoice parser: {len(rows)} rows')
    return rows

# ═══════════════════════════════════════════════════════
# STEP 2B: AI VISION EXTRACTION (smart path — GPT-4o)
# ═══════════════════════════════════════════════════════

AI_PROMPTS = {
    'bank_statement': """You are extracting BANK STATEMENT transactions.
Extract EVERY transaction row. For each row return:
- date: transaction date in YYYY-MM-DD format
- description: narration/description of transaction (no amounts in description)
- amount: POSITIVE number only, no currency symbols, no commas (e.g. 1500.00)
- type: "debit" if money left the account, "credit" if money came in
- category: one of: food, transport, utilities, salary, rent, transfer, shopping, healthcare, education, entertainment, other
- gst: 0 (bank statements rarely show GST)
- reference: UTR/cheque/transaction reference if visible, else ""

RETURN ONLY THIS JSON. NO TEXT BEFORE OR AFTER. NO MARKDOWN:
{"document_type":"bank_statement","rows":[{"date":"","description":"","amount":0,"type":"debit","category":"","gst":0,"reference":""}]}""",

    'invoice': """You are extracting INVOICE line items.
Extract EVERY item/service line. For each row return:
- date: invoice date in YYYY-MM-DD format (same for all rows if one invoice)
- description: item or service name
- amount: line total as POSITIVE number, no currency symbols, no commas
- type: "expense"
- category: infer from description (software, consulting, supplies, services, other)
- gst: GST/tax amount for that line as POSITIVE number, 0 if not shown
- reference: item code, HSN code, or SKU if visible, else ""

RETURN ONLY THIS JSON. NO TEXT BEFORE OR AFTER. NO MARKDOWN:
{"document_type":"invoice","rows":[{"date":"","description":"","amount":0,"type":"expense","category":"","gst":0,"reference":""}]}""",

    'receipt': """You are extracting RECEIPT items.
Extract EVERY purchased item. For each row return:
- date: purchase date in YYYY-MM-DD format
- description: item name
- amount: item price as POSITIVE number, no currency symbols
- type: "expense"
- category: infer from item name
- gst: tax on item if shown, else 0
- reference: receipt number on first row only, else ""

RETURN ONLY THIS JSON. NO TEXT BEFORE OR AFTER. NO MARKDOWN:
{"document_type":"receipt","rows":[{"date":"","description":"","amount":0,"type":"expense","category":"","gst":0,"reference":""}]}""",

    'table': """You are extracting data from a TABLE or SPREADSHEET image.
Extract EVERY data row (skip header rows). Map columns to closest field:
- date: any date column
- description: main text/name column
- amount: primary numeric column as POSITIVE number
- type: "debit" or "credit" or "expense" based on context
- category: infer from description
- gst: tax column if present, else 0
- reference: ID/reference column if present, else ""

RETURN ONLY THIS JSON. NO TEXT BEFORE OR AFTER. NO MARKDOWN:
{"document_type":"table","rows":[{"date":"","description":"","amount":0,"type":"debit","category":"","gst":0,"reference":""}]}""",

    'other': """You are extracting structured financial data from a document.
Extract EVERY row of financial data visible. Return:
- date: date string in YYYY-MM-DD if possible
- description: what the entry is for
- amount: POSITIVE number, no symbols or commas
- type: "debit", "credit", "expense", or "income"
- category: best guess category
- gst: tax amount if visible, else 0
- reference: reference number if visible, else ""

RETURN ONLY THIS JSON. NO TEXT BEFORE OR AFTER. NO MARKDOWN:
{"document_type":"other","rows":[{"date":"","description":"","amount":0,"type":"debit","category":"","gst":0,"reference":""}]}"""
}

RETRY_PROMPTS = [
    # Retry 1: Simplified prompt
    """Extract ALL financial data from this document into structured JSON.
Return ONLY valid JSON with this exact structure:
{"rows":[{"date":"","description":"","amount":0,"type":"debit","gst":0,"reference":"","category":""}]}
Rules: amounts are plain positive numbers. Extract every visible data row. No markdown.""",

    # Retry 2: Ultra-simplified prompt
    """Look at this document carefully. Find every row of data.
Return JSON only: {"rows":[{"date":"","description":"","amount":0,"type":"debit"}]}
Keep numbers exact. No text outside JSON.""",

    # Retry 3: Raw text extraction fallback
    """Read ALL text visible in this document. Return it as structured rows.
For each line of data, create: {"date":"","description":"the text","amount":0,"type":"other"}
Return: {"rows":[...], "raw_text": "first 500 chars of visible text"}
If you cannot find structured data, still return raw_text with everything you can read.""",
]


async def ai_extract_image(image_path, doc_type, user_requirements=''):
    """AI Vision extraction from image file."""
    try:
        with open(image_path, 'rb') as f:
            img_b64 = base64.b64encode(f.read()).decode('utf-8')

        system = AI_PROMPTS.get(doc_type, AI_PROMPTS['other'])
        if user_requirements and user_requirements.strip():
            system += f"\nUSER REQUIREMENTS: {user_requirements}\nPrioritize extracting fields that match these requirements."

        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all financial data from this document. Return ONLY the JSON."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]
            }
        ]

        log_step('ai_extract', f'Calling GPT-4o vision for {doc_type}')
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=4000,
            temperature=0
        )
        result = safe_parse_json(response.choices[0].message.content)
        if result:
            row_count = len(result.get('rows', []))
            log_step('ai_extract', f'AI returned {row_count} rows')
        return result
    except Exception as e:
        log_step('ai_extract', f'AI image extraction failed: {e}')
        return None


async def ai_extract_text(text, doc_type, user_requirements=''):
    """AI text extraction for text PDFs where rule-based fails."""
    try:
        system = AI_PROMPTS.get(doc_type, AI_PROMPTS['other'])
        if user_requirements and user_requirements.strip():
            system += f"\nUSER REQUIREMENTS: {user_requirements}\nPrioritize extracting fields that match these requirements."

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Extract all financial data from this document text. Return ONLY the JSON.\n\n{text[:12000]}"}
        ]

        log_step('ai_extract', f'Calling GPT-4o text for {doc_type}')
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=4000,
            temperature=0
        )
        result = safe_parse_json(response.choices[0].message.content)
        if result:
            row_count = len(result.get('rows', []))
            log_step('ai_extract', f'AI text returned {row_count} rows')
        return result
    except Exception as e:
        log_step('ai_extract', f'AI text extraction failed: {e}')
        return None


async def ai_retry(content, is_image, attempt=0):
    """Multi-attempt retry with progressively simpler prompts."""
    prompt = RETRY_PROMPTS[min(attempt, len(RETRY_PROMPTS) - 1)]
    try:
        if is_image:
            with open(content, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')
            messages = [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract data. Return JSON only."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]
                }
            ]
        else:
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Extract data. Return JSON only.\n\n{str(content)[:8000]}"}
            ]

        log_step('retry', f'Retry attempt {attempt + 1}/3')
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=4000,
            temperature=0
        )
        result = safe_parse_json(response.choices[0].message.content)
        if result:
            row_count = len(result.get('rows', []))
            log_step('retry', f'Retry {attempt + 1} returned {row_count} rows')
        return result
    except Exception as e:
        log_step('retry', f'Retry {attempt + 1} failed: {e}')
        return None

# ═══════════════════════════════════════════════════════
# STEP 3: JSON PARSING — DEFENSIVE
# ═══════════════════════════════════════════════════════

def safe_parse_json(response):
    if not response:
        return None
    text = response.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code blocks
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find outermost JSON object
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    # Try to fix common issues
    try:
        # Remove trailing commas
        fixed = re.sub(r',\s*([}\]])', r'\1', text)
        return json.loads(fixed)
    except (json.JSONDecodeError, Exception):
        pass

    log_step('json_parse', f'Failed to parse JSON: {text[:200]}')
    return None

# ═══════════════════════════════════════════════════════
# STEP 4: VALIDATION ENGINE
# ═══════════════════════════════════════════════════════

def validate_and_clean_number(val):
    """Convert any amount value to a clean positive float."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return round(abs(float(val)), 2)
    cleaned = re.sub(r'[^\d.]', '', str(val))
    parts = cleaned.split('.')
    if len(parts) > 2:
        cleaned = parts[0] + '.' + ''.join(parts[1:])
    try:
        return round(abs(float(cleaned)), 2) if cleaned else 0.0
    except ValueError:
        return 0.0

def normalize_date_str(val):
    """Parse any date format to YYYY-MM-DD."""
    if not val or not str(val).strip():
        return ''
    val = str(val).strip()
    if re.match(r'^\d{4}-\d{2}-\d{2}$', val):
        return val
    try:
        from dateutil import parser as dp
        return dp.parse(val, dayfirst=True).strftime('%Y-%m-%d')
    except Exception:
        pass
    patterns = [
        (r'(\d{2})[\/\-\.](\d{2})[\/\-\.](\d{4})', lambda m: f'{m.group(3)}-{m.group(2)}-{m.group(1)}'),
        (r'(\d{2})[\/\-\.](\d{2})[\/\-\.](\d{2})', lambda m: f'20{m.group(3)}-{m.group(2)}-{m.group(1)}'),
        (r'(\d{4})[\/\-\.](\d{2})[\/\-\.](\d{2})', lambda m: f'{m.group(1)}-{m.group(2)}-{m.group(3)}'),
    ]
    for pattern, formatter in patterns:
        m = re.search(pattern, val)
        if m:
            try:
                return formatter(m)
            except Exception:
                pass
    return val

def validate_type(val, amount, description):
    """Ensure type is always one of the valid values."""
    if not val:
        val = ''
    val_lower = val.lower().strip()
    if val_lower in ('debit', 'credit', 'expense', 'income'):
        return val_lower
    desc_lower = description.lower()
    if any(w in desc_lower for w in ['salary', 'income', 'received', 'credit', 'refund', 'cashback']):
        return 'credit'
    if any(w in desc_lower for w in ['payment', 'purchase', 'paid', 'debit', 'withdraw', 'charge']):
        return 'debit'
    return 'debit'

def infer_category(description):
    """Keyword-based category inference."""
    desc = description.lower()
    if any(w in desc for w in ['zomato', 'swiggy', 'restaurant', 'hotel', 'cafe', 'food', 'dining', 'meal']):
        return 'food'
    if any(w in desc for w in ['uber', 'ola', 'petrol', 'fuel', 'cab', 'taxi', 'metro', 'bus', 'train', 'flight', 'airfare']):
        return 'transport'
    if any(w in desc for w in ['electricity', 'water', 'gas', 'broadband', 'internet', 'mobile', 'recharge', 'wifi', 'utility']):
        return 'utilities'
    if any(w in desc for w in ['salary', 'wages', 'payroll', 'stipend', 'income', 'bonus']):
        return 'salary'
    if any(w in desc for w in ['rent', 'lease', 'housing', 'flat', 'apartment', 'maintenance', 'society']):
        return 'rent'
    if any(w in desc for w in ['neft', 'imps', 'rtgs', 'transfer', 'fund transfer', 'upi']):
        return 'transfer'
    if any(w in desc for w in ['amazon', 'flipkart', 'myntra', 'shopping', 'retail', 'purchase', 'store']):
        return 'shopping'
    if any(w in desc for w in ['hospital', 'doctor', 'medical', 'pharmacy', 'health', 'clinic', 'labs']):
        return 'healthcare'
    if any(w in desc for w in ['school', 'college', 'university', 'course', 'fees', 'education', 'tuition']):
        return 'education'
    if any(w in desc for w in ['netflix', 'spotify', 'entertainment', 'movie', 'game', 'subscription']):
        return 'entertainment'
    return 'other'

def validate_rows(rows):
    """Full validation pass on all rows."""
    validated = []
    seen = set()

    for row in rows:
        if not isinstance(row, dict):
            continue

        date = normalize_date_str(str(row.get('date', '')))
        description = str(row.get('description', '')).strip()
        amount = validate_and_clean_number(row.get('amount', 0))
        gst = validate_and_clean_number(row.get('gst', 0))
        tx_type = validate_type(str(row.get('type', '')), amount, description)
        reference = str(row.get('reference', '')).strip()[:100]
        category = str(row.get('category', '')).strip()

        if not description and amount == 0:
            continue
        if description.lower() in ('', 'nan', 'none', 'null', '-', 'n/a'):
            continue
        if description.lower() in ('description', 'particulars', 'narration', 'details', 'item'):
            continue

        if not description and amount > 0:
            description = 'Transaction'

        if not category or category == 'other':
            category = infer_category(description)

        dedup_key = (date, description[:50].lower(), amount)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        confidence = calculate_confidence(date, description, amount, tx_type)

        validated.append({
            'date': date,
            'description': description[:300],
            'amount': amount,
            'type': tx_type,
            'category': category,
            'gst': gst,
            'reference': reference,
            'confidence': confidence,
        })

    log_step('validate', f'Validated {len(validated)} rows from {len(rows)} raw rows')
    return validated

# ═══════════════════════════════════════════════════════
# STEP 5: NORMALIZATION
# ═══════════════════════════════════════════════════════

def normalize_result(rows, doc_type, user_requirements=''):
    """Build the final normalized output object."""
    for i, row in enumerate(rows):
        row['row_number'] = i + 1

    total_amount = sum(r['amount'] for r in rows)
    total_gst = sum(r['gst'] for r in rows)
    avg_confidence = (sum(r['confidence'] for r in rows) / len(rows)) if rows else 0

    result = {
        'document_type': doc_type,
        'rows': rows,
        'summary': {
            'total_rows': len(rows),
            'total_amount': round(total_amount, 2),
            'total_gst': round(total_gst, 2),
            'currency': 'INR',
            'avg_confidence': round(avg_confidence, 3),
        },
        'confidence_score': round(avg_confidence, 3),
    }
    if user_requirements and user_requirements.strip():
        result['user_requirements'] = user_requirements.strip()
    return result

# ═══════════════════════════════════════════════════════
# STEP 6: CONFIDENCE SCORING PER ROW
# ═══════════════════════════════════════════════════════

def calculate_confidence(date, description, amount, tx_type):
    score = 0.0
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date):
        score += 0.30
    elif date:
        score += 0.15
    if len(description) > 5:
        score += 0.25
    elif description:
        score += 0.10
    if amount > 0:
        score += 0.30
    if tx_type in ('debit', 'credit', 'expense', 'income'):
        score += 0.15
    return round(min(score, 1.0), 3)

# ═══════════════════════════════════════════════════════
# STEP 7: POST-PROCESSING INSTRUCTION ENGINE
# ═══════════════════════════════════════════════════════

def apply_instructions(rows, user_requirements):
    """
    Apply user instructions AFTER extraction.
    Supports: remove, rename, filter, group, ignore, add field.
    Returns modified rows.
    """
    if not user_requirements or not user_requirements.strip():
        return rows

    instructions = user_requirements.lower().strip()
    original_count = len(rows)

    # REMOVE / IGNORE: "remove transactions below ₹1000", "ignore amounts less than 500"
    # Remove below threshold
    match = re.search(r'(?:remove|delete|ignore|exclude)\s+.*?(?:below|under|less than|<)\s*[₹$Rs. ]*(\d+(?:,\d+)*(?:\.\d+)?)', instructions)
    if match:
        threshold = float(match.group(1).replace(',', ''))
        rows = [r for r in rows if r.get('amount', 0) >= threshold]
        log_step('instruct', f'Removed rows with amount < {threshold} ({original_count - len(rows)} removed)')

    # Remove above threshold
    match = re.search(r'(?:remove|delete|ignore|exclude)\s+.*?(?:above|over|greater than|more than|>)\s*[₹$Rs. ]*(\d+(?:,\d+)*(?:\.\d+)?)', instructions)
    if match:
        threshold = float(match.group(1).replace(',', ''))
        rows = [r for r in rows if r.get('amount', 0) <= threshold]
        log_step('instruct', f'Removed rows with amount > {threshold}')

    # ONLY INCLUDE / FILTER: "only include GST items", "only show debits"
    if re.search(r'only\s+(?:include|show|keep)\s+(?:.*?)(?:debit|withdrawal)', instructions):
        rows = [r for r in rows if r.get('type') in ('debit', 'expense')]
        log_step('instruct', f'Filtered to debit/expense only: {len(rows)} rows')
    elif re.search(r'only\s+(?:include|show|keep)\s+(?:.*?)(?:credit|income|deposit)', instructions):
        rows = [r for r in rows if r.get('type') in ('credit', 'income')]
        log_step('instruct', f'Filtered to credit/income only: {len(rows)} rows')

    # Filter by GST
    if re.search(r'only\s+(?:include|show|keep)\s+(?:.*?)gst', instructions):
        rows = [r for r in rows if r.get('gst', 0) > 0]
        log_step('instruct', f'Filtered to GST items only: {len(rows)} rows')

    # Filter by category keyword
    category_match = re.search(r'only\s+(?:include|show|keep)\s+(?:.*?)(food|transport|utilities|salary|rent|transfer|shopping|healthcare|education|entertainment)', instructions)
    if category_match:
        cat = category_match.group(1)
        rows = [r for r in rows if r.get('category', '').lower() == cat]
        log_step('instruct', f'Filtered to category "{cat}": {len(rows)} rows')

    # RENAME: "rename description to narration", "rename amount to total"
    rename_match = re.findall(r'rename\s+(?:column\s+)?(\w+)\s+to\s+(\w+)', instructions)
    if rename_match:
        for old_name, new_name in rename_match:
            for r in rows:
                if old_name in r:
                    r[new_name] = r.pop(old_name)
            log_step('instruct', f'Renamed column "{old_name}" → "{new_name}"')

    # GROUP BY: "group by category", "group by type"
    group_match = re.search(r'group\s+by\s+(\w+)', instructions)
    if group_match:
        group_field = group_match.group(1)
        if group_field in ('category', 'type', 'date'):
            groups = {}
            for r in rows:
                key = r.get(group_field, 'other')
                if key not in groups:
                    groups[key] = {'description': f'Group: {key}', 'amount': 0, 'gst': 0, 'type': 'debit', 'category': key if group_field == 'category' else '', 'date': '', 'reference': '', 'confidence': 0.9, '_count': 0}
                groups[key]['amount'] = round(groups[key]['amount'] + r.get('amount', 0), 2)
                groups[key]['gst'] = round(groups[key]['gst'] + r.get('gst', 0), 2)
                groups[key]['_count'] += 1
            # Build grouped rows with counts in description
            grouped_rows = []
            for key, data in groups.items():
                data['description'] = f'{key} ({data["_count"]} transactions)'
                del data['_count']
                grouped_rows.append(data)
            rows = grouped_rows
            log_step('instruct', f'Grouped by "{group_field}": {len(rows)} groups')

    # SORT: "sort by amount", "sort by date"
    sort_match = re.search(r'sort\s+by\s+(\w+)\s*(asc|desc|ascending|descending)?', instructions)
    if sort_match:
        sort_field = sort_match.group(1)
        direction = sort_match.group(2) or 'asc'
        reverse = direction.startswith('desc')
        if sort_field in ('amount', 'gst', 'date', 'description', 'category'):
            rows = sorted(rows, key=lambda r: r.get(sort_field, ''), reverse=reverse)
            log_step('instruct', f'Sorted by "{sort_field}" {"desc" if reverse else "asc"}')

    log_step('instruct', f'Instructions applied: {original_count} → {len(rows)} rows')
    return rows

# ═══════════════════════════════════════════════════════
# STEP 8: MULTI-RETRY PIPELINE + NEVER FAIL
# ═══════════════════════════════════════════════════════

async def run_extraction_pipeline(file_path, user_requirements, is_image, text_content=''):
    """
    Full pipeline with 3-attempt retry and never-fail guarantee:
    1. Detect document type
    2. Try text parse (if text available)
    3. Run AI extraction with type-specific prompt
    4. Validate + normalize
    5. If poor results → retry up to 3 times with simpler prompts
    6. If still no results → return raw text as partial result
    7. Apply user instructions post-extraction
    NEVER returns error - always returns at least partial data
    """

    # DETECT type
    if text_content:
        doc_type = detect_document_type_from_text(text_content)
    else:
        doc_type = 'other'

    rows = []
    ai_doc_type = doc_type
    raw_text_fallback = text_content[:2000] if text_content else ''

    # PATH A: Text PDF — try rule-based parser first
    if text_content and not is_image:
        log_step('pipeline', f'Text path, detected type: {doc_type}')

        if doc_type == 'bank_statement':
            rows = parse_bank_statement_text(text_content)
        elif doc_type in ('invoice', 'receipt'):
            rows = parse_invoice_text(text_content)

        if len(rows) >= 3:
            log_step('pipeline', f'Rule-based got {len(rows)} rows, running AI to validate')
            ai_result = await ai_extract_text(text_content, doc_type, user_requirements)
            if ai_result and isinstance(ai_result.get('rows'), list) and len(ai_result['rows']) > len(rows):
                log_step('pipeline', f'AI got more rows ({len(ai_result["rows"])}), using AI result')
                rows = ai_result['rows']
                ai_doc_type = ai_result.get('document_type', doc_type)
            else:
                ai_doc_type = doc_type
        else:
            log_step('pipeline', f'Rule-based got {len(rows)} rows, falling back to AI')
            ai_result = await ai_extract_text(text_content, doc_type, user_requirements)
            if ai_result and isinstance(ai_result.get('rows'), list):
                rows = ai_result['rows']
                ai_doc_type = ai_result.get('document_type', doc_type)

    # PATH B: Image or scanned PDF — AI vision
    else:
        log_step('pipeline', 'Image/scanned path')
        ai_result = await ai_extract_image(file_path, doc_type, user_requirements)
        if ai_result and isinstance(ai_result.get('rows'), list):
            rows = ai_result['rows']
            ai_doc_type = ai_result.get('document_type', doc_type)

    # VALIDATE
    validated_rows = validate_rows(rows)
    avg_conf = (sum(r['confidence'] for r in validated_rows) / len(validated_rows)) if validated_rows else 0

    # MULTI-RETRY: up to 3 attempts if results are poor
    retry_count = 0
    while (len(validated_rows) < 2 or avg_conf < 0.35) and retry_count < 3:
        log_step('pipeline', f'Poor results ({len(validated_rows)} rows, conf {avg_conf:.2f}), retry {retry_count + 1}/3')
        retry_result = await ai_retry(
            file_path if is_image else text_content,
            is_image,
            attempt=retry_count
        )
        if retry_result and isinstance(retry_result.get('rows'), list):
            retry_rows = validate_rows(retry_result['rows'])
            if len(retry_rows) > len(validated_rows):
                validated_rows = retry_rows
                avg_conf = (sum(r['confidence'] for r in validated_rows) / len(validated_rows)) if validated_rows else 0
                log_step('pipeline', f'Retry {retry_count + 1} improved to {len(validated_rows)} rows, conf {avg_conf:.2f}')
            # Also capture raw text from retry
            if retry_result.get('raw_text') and not raw_text_fallback:
                raw_text_fallback = retry_result['raw_text']
        retry_count += 1

    # NEVER FAIL: If still no rows, create partial result from raw text
    if not validated_rows:
        log_step('pipeline', 'All extraction attempts failed, creating partial result from raw text')
        if raw_text_fallback:
            # Create a single row with raw text as description
            lines = [ln.strip() for ln in raw_text_fallback.split('\n') if ln.strip() and len(ln.strip()) > 3]
            for i, line in enumerate(lines[:50]):  # Max 50 rows from raw text
                validated_rows.append({
                    'date': '',
                    'description': line[:300],
                    'amount': 0,
                    'type': 'other',
                    'category': 'other',
                    'gst': 0,
                    'reference': '',
                    'confidence': 0.15,  # Very low confidence for raw text
                })
            log_step('pipeline', f'Created {len(validated_rows)} partial rows from raw text')
        else:
            # Absolute last resort - return at least something
            validated_rows.append({
                'date': '',
                'description': 'Document uploaded but could not be fully extracted. Please edit manually.',
                'amount': 0,
                'type': 'other',
                'category': 'other',
                'gst': 0,
                'reference': '',
                'confidence': 0.05,
            })
            log_step('pipeline', 'Created placeholder row - document needs manual editing')

    # APPLY USER INSTRUCTIONS (post-processing)
    if user_requirements:
        validated_rows = apply_instructions(validated_rows, user_requirements)

    result = normalize_result(validated_rows, ai_doc_type, user_requirements)

    # Add partial flag if confidence is very low
    if result['confidence_score'] < 0.3:
        result['partial'] = True
        result['partial_message'] = 'Partial result ready — some data may need manual editing. Low-confidence rows are highlighted.'

    log_step('pipeline', f'Final: {len(validated_rows)} rows, conf {result["confidence_score"]:.3f}')
    return result

# ═══════════════════════════════════════════════════════
# MAIN HANDLERS PER FILE TYPE
# ═══════════════════════════════════════════════════════

async def handle_image(file_path, user_requirements):
    return await run_extraction_pipeline(file_path, user_requirements, is_image=True)

async def handle_pdf(file_path, user_requirements):
    text, is_scanned, total_page_count = extract_text_from_pdf(file_path)

    if is_scanned or len(text.strip()) < 80:
        log_step('pdf', 'Scanned PDF — converting to images')
        try:
            import pdfplumber
            all_rows = []
            best_doc_type = 'other'

            with pdfplumber.open(file_path) as pdf:
                total_page_count = len(pdf.pages)
                pages_to_process = min(len(pdf.pages), 6)

                # PARALLEL page processing with asyncio.gather
                async def process_page(page_num, page):
                    try:
                        img = page.to_image(resolution=220)
                        tmp_path = f'{file_path}_page{page_num}.png'
                        img.original.save(tmp_path, format='PNG')
                        page_result = await run_extraction_pipeline(tmp_path, user_requirements, is_image=True)
                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass
                        return page_num, page_result
                    except Exception as pe:
                        log_step('pdf', f'Page {page_num} error: {pe}')
                        return page_num, None

                # Process pages in parallel (max 3 concurrent)
                semaphore = asyncio.Semaphore(3)
                async def limited_process(page_num, page):
                    async with semaphore:
                        return await process_page(page_num, page)

                tasks = [limited_process(i, pdf.pages[i]) for i in range(pages_to_process)]
                results = await asyncio.gather(*tasks)

                for page_num, page_result in sorted(results, key=lambda x: x[0]):
                    if page_result and 'rows' in page_result:
                        all_rows.extend(page_result['rows'])
                        if page_num == 0:
                            best_doc_type = page_result.get('document_type', 'other')

            if all_rows:
                validated = validate_rows(all_rows)
                # Apply instructions after combining all pages
                if user_requirements:
                    validated = apply_instructions(validated, user_requirements)
                result = normalize_result(validated, best_doc_type, user_requirements)
                if total_page_count > 6:
                    result["page_warning"] = (
                        f"Only the first 6 of {total_page_count} pages were processed. "
                        "To extract all data, split your PDF into parts and upload each separately."
                    )
                return result

            # Never fail: even if all pages failed, return something
            log_step('pdf', 'All pages failed, returning partial result')
            return normalize_result([{
                'date': '',
                'description': 'Scanned PDF could not be fully processed. Try uploading a clearer scan.',
                'amount': 0, 'type': 'other', 'category': 'other', 'gst': 0, 'reference': '',
                'confidence': 0.05,
            }], 'other', user_requirements)

        except Exception as e:
            log_step('pdf', f'Image conversion failed: {e}')
            return normalize_result([{
                'date': '',
                'description': 'PDF processing encountered an error. Please try uploading as an image.',
                'amount': 0, 'type': 'other', 'category': 'other', 'gst': 0, 'reference': '',
                'confidence': 0.05,
            }], 'other', user_requirements)
    else:
        log_step('pdf', f'Text PDF, {len(text)} chars extracted')
        result = await run_extraction_pipeline(file_path, user_requirements, is_image=False, text_content=text)
        if total_page_count > 6 and result and 'rows' in result:
            result["page_warning"] = (
                f"Only the first 6 of {total_page_count} pages were processed. "
                "To extract all data, split your PDF into parts and upload each separately."
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
            result = normalize_result([{
                'date': '',
                'description': f'Unsupported file type: {ext}. Supported: PDF, JPG, PNG, WEBP',
                'amount': 0, 'type': 'other', 'category': 'other', 'gst': 0, 'reference': '',
                'confidence': 0.05,
            }], 'other', user_requirements)

        # Add processing metadata
        elapsed = round(time.time() - start_time, 2)
        result['processing_time_seconds'] = elapsed
        result['pipeline_log'] = LOG_STEPS
        log_step('done', f'Completed in {elapsed}s')

        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        log_step('fatal', f'Fatal error: {e}')
        # NEVER FAIL: return partial result even on crash
        elapsed = round(time.time() - start_time, 2)
        fallback = normalize_result([{
            'date': '',
            'description': 'Extraction encountered an unexpected error. Please try again or use a different file format.',
            'amount': 0, 'type': 'other', 'category': 'other', 'gst': 0, 'reference': '',
            'confidence': 0.05,
        }], 'other', user_requirements)
        fallback['partial'] = True
        fallback['partial_message'] = 'Partial result — document could not be fully processed.'
        fallback['processing_time_seconds'] = elapsed
        print(json.dumps(fallback, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(main())
