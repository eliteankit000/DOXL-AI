#!/usr/bin/env python3
"""
DocXL AI — Production Extraction Engine v2.0
Architecture: Detect -> Dual Extract -> Validate -> Normalize -> Score -> Retry
Target: 90-95% accuracy
Uses OpenAI GPT-4o directly (no proxy)
"""
import sys
import os
import json
import base64
import asyncio
import re
import io
from pathlib import Path
from datetime import datetime
from openai import AsyncOpenAI

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
if not OPENAI_API_KEY:
    print(json.dumps({"error": "OPENAI_API_KEY not configured"}))
    sys.exit(1)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

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
    if scores[best] >= 2:
        return best
    return 'table'

# ═══════════════════════════════════════════════════════
# STEP 2A: TEXT PDF PARSER (fast path — pdfplumber)
# ═══════════════════════════════════════════════════════

def extract_text_from_pdf(file_path):
    """Returns (text, is_scanned). is_scanned=True means text extraction failed."""
    try:
        import pdfplumber
        text = ''
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
        if len(text.strip()) > 80:
            return text, False
        return text, True
    except Exception as e:
        print(f'[pdf_text] failed: {e}', file=sys.stderr)
        return '', True

def parse_bank_statement_text(text):
    """Rule-based parser for bank statement text — handles common formats."""
    rows = []
    lines = [l.strip() for l in text.split('\n') if l.strip()]

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

    return rows

def parse_invoice_text(text):
    """Rule-based parser for invoice text."""
    rows = []
    lines = [l.strip() for l in text.split('\n') if l.strip()]

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

RETRY_PROMPT = """Extract financial data from this document.
Return ONLY valid JSON with this exact structure, nothing else:
{"rows":[{"date":"","description":"","amount":0,"type":"debit","gst":0}]}
Rules: amounts are plain numbers, no symbols. Extract every row."""


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

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=4000,
            temperature=0
        )
        return safe_parse_json(response.choices[0].message.content)
    except Exception as e:
        print(f'[ai_extract_image] failed: {e}', file=sys.stderr)
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

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=4000,
            temperature=0
        )
        return safe_parse_json(response.choices[0].message.content)
    except Exception as e:
        print(f'[ai_extract_text] failed: {e}', file=sys.stderr)
        return None


async def ai_retry(content, is_image):
    """Simpler fallback prompt for retry."""
    try:
        if is_image:
            with open(content, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')
            messages = [
                {"role": "system", "content": RETRY_PROMPT},
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
                {"role": "system", "content": RETRY_PROMPT},
                {"role": "user", "content": f"Extract data. Return JSON only.\n\n{str(content)[:8000]}"}
            ]

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=4000,
            temperature=0
        )
        return safe_parse_json(response.choices[0].message.content)
    except Exception as e:
        print(f'[ai_retry] failed: {e}', file=sys.stderr)
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

    print(f'[safe_parse_json] failed on: {text[:300]}', file=sys.stderr)
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
# STEP 7: RETRY + FALLBACK SYSTEM
# ═══════════════════════════════════════════════════════

async def run_extraction_pipeline(file_path, user_requirements, is_image, text_content=''):
    """
    Full pipeline:
    1. Detect document type
    2. Try text parse (if text available)
    3. Run AI extraction with type-specific prompt
    4. Validate + normalize
    5. If low confidence or too few rows -> retry with simpler prompt
    6. Merge best results
    """

    # DETECT type
    if text_content:
        doc_type = detect_document_type_from_text(text_content)
    else:
        doc_type = 'other'

    rows = []
    ai_doc_type = doc_type

    # PATH A: Text PDF — try rule-based parser first
    if text_content and not is_image:
        print(f'[pipeline] text path, detected type: {doc_type}', file=sys.stderr)

        if doc_type == 'bank_statement':
            rows = parse_bank_statement_text(text_content)
        elif doc_type in ('invoice', 'receipt'):
            rows = parse_invoice_text(text_content)

        if len(rows) >= 3:
            print(f'[pipeline] rule-based got {len(rows)} rows, running AI to validate', file=sys.stderr)
            ai_result = await ai_extract_text(text_content, doc_type, user_requirements)
            if ai_result and isinstance(ai_result.get('rows'), list) and len(ai_result['rows']) > len(rows):
                print(f'[pipeline] AI got more rows ({len(ai_result["rows"])}), using AI result', file=sys.stderr)
                rows = ai_result['rows']
                ai_doc_type = ai_result.get('document_type', doc_type)
            else:
                ai_doc_type = doc_type
        else:
            print(f'[pipeline] rule-based got {len(rows)} rows, falling back to AI', file=sys.stderr)
            ai_result = await ai_extract_text(text_content, doc_type, user_requirements)
            if ai_result and isinstance(ai_result.get('rows'), list):
                rows = ai_result['rows']
                ai_doc_type = ai_result.get('document_type', doc_type)

    # PATH B: Image or scanned PDF — AI vision
    else:
        print(f'[pipeline] image/scanned path', file=sys.stderr)
        ai_result = await ai_extract_image(file_path, doc_type, user_requirements)
        if ai_result and isinstance(ai_result.get('rows'), list):
            rows = ai_result['rows']
            ai_doc_type = ai_result.get('document_type', doc_type)

    # VALIDATE
    validated_rows = validate_rows(rows)
    avg_conf = (sum(r['confidence'] for r in validated_rows) / len(validated_rows)) if validated_rows else 0

    # RETRY if results are poor
    if len(validated_rows) < 2 or avg_conf < 0.35:
        print(f'[pipeline] poor results ({len(validated_rows)} rows, conf {avg_conf:.2f}), retrying...', file=sys.stderr)
        retry_result = await ai_retry(
            file_path if is_image else text_content,
            is_image
        )
        if retry_result and isinstance(retry_result.get('rows'), list):
            retry_rows = validate_rows(retry_result['rows'])
            if len(retry_rows) > len(validated_rows):
                validated_rows = retry_rows
                print(f'[pipeline] retry improved to {len(validated_rows)} rows', file=sys.stderr)

    if not validated_rows:
        return {'error': 'Could not extract any data from this document. Please ensure the document is clear, not password-protected, and contains tabular financial data.'}

    return normalize_result(validated_rows, ai_doc_type, user_requirements)

# ═══════════════════════════════════════════════════════
# MAIN HANDLERS PER FILE TYPE
# ═══════════════════════════════════════════════════════

async def handle_image(file_path, user_requirements):
    return await run_extraction_pipeline(file_path, user_requirements, is_image=True)

async def handle_pdf(file_path, user_requirements):
    text, is_scanned = extract_text_from_pdf(file_path)

    if is_scanned or len(text.strip()) < 80:
        print('[handle_pdf] scanned PDF — converting to images', file=sys.stderr)
        try:
            import pdfplumber
            all_rows = []
            best_doc_type = 'other'
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages[:6]):
                    try:
                        img = page.to_image(resolution=220)
                        tmp_path = f'{file_path}_page{page_num}.png'
                        img.original.save(tmp_path, format='PNG')
                        page_result = await run_extraction_pipeline(tmp_path, user_requirements, is_image=True)
                        os.remove(tmp_path)
                        if page_result and 'rows' in page_result:
                            all_rows.extend(page_result['rows'])
                            if page_num == 0:
                                best_doc_type = page_result.get('document_type', 'other')
                    except Exception as pe:
                        print(f'[handle_pdf] page {page_num} error: {pe}', file=sys.stderr)
                        continue

            if all_rows:
                validated = validate_rows(all_rows)
                return normalize_result(validated, best_doc_type)
            return {'error': 'Could not extract data from this scanned PDF. Try uploading a clearer scan or a text-based PDF.'}
        except Exception as e:
            print(f'[handle_pdf] image conversion failed: {e}', file=sys.stderr)
            return {'error': 'PDF processing failed. Please try uploading an image of the document.'}
    else:
        print(f'[handle_pdf] text PDF, {len(text)} chars extracted', file=sys.stderr)
        return await run_extraction_pipeline(file_path, user_requirements, is_image=False, text_content=text)

# ═══════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════

async def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'No file path provided'}))
        sys.exit(1)

    file_path = sys.argv[1]
    user_requirements = sys.argv[2] if len(sys.argv) > 2 else ''

    if not os.path.exists(file_path):
        print(json.dumps({'error': f'File not found: {file_path}'}))
        sys.exit(1)

    ext = Path(file_path).suffix.lower()

    try:
        if ext in ('.jpg', '.jpeg', '.png', '.webp'):
            result = await handle_image(file_path, user_requirements)
        elif ext == '.pdf':
            result = await handle_pdf(file_path, user_requirements)
        else:
            result = {'error': f'Unsupported file type: {ext}. Supported: PDF, JPG, PNG, WEBP'}

        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(f'[main] fatal error: {e}', file=sys.stderr)
        print(json.dumps({'error': 'Extraction failed. Please try again.'}))
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
