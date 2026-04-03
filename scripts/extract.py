#!/usr/bin/env python3
"""
DocXL AI - Enhanced Document Extraction Script
3-pass pipeline: detect -> extract -> validate+correct
Uses OpenAI GPT-4o directly (no proxy)
"""
import sys
import os
import json
import base64
import asyncio
import re
from pathlib import Path
from openai import AsyncOpenAI

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
if not OPENAI_API_KEY:
    print(json.dumps({"error": "OPENAI_API_KEY not configured"}), file=sys.stderr)
    sys.exit(1)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# -- Type-specific extraction prompts --

TYPE_PROMPTS = {
    "invoice": """You are extracting data from an INVOICE. Extract every line item.
Fields: date (invoice date), description (item/service name), amount (unit price or line total as plain number),
type (always "expense"), category (infer from description), gst (tax amount as plain number), reference (item code or SKU if visible).
If quantity and unit price are both shown, multiply them for amount.""",

    "bank_statement": """You are extracting data from a BANK STATEMENT. Extract every transaction row.
Fields: date (transaction date YYYY-MM-DD), description (merchant/narration), amount (absolute value, plain number),
type ("debit" if money left account, "credit" if money came in), category (infer: food/transport/utilities/salary/transfer/other),
gst (0 unless explicitly shown), reference (transaction ID, cheque number, or UTR if visible).""",

    "receipt": """You are extracting data from a RECEIPT. Extract every purchased item.
Fields: date (purchase date), description (item name), amount (item total as plain number),
type (always "expense"), category (infer from store/item type), gst (tax on that item if shown, else 0),
reference (receipt number if visible on first row, else empty).""",

    "table": """You are extracting data from a TABLE or SPREADSHEET IMAGE. Extract every data row, ignoring header rows.
Map visible columns to the closest matching fields: date, description, amount (plain number), type, category, gst (plain number), reference.
If a column has no clear match, put its value in description.""",

    "other": """You are extracting structured financial data from a document.
Extract every row of data you can find. Use fields: date, description, amount (plain number), type (debit/credit/expense/income),
category, gst (plain number, 0 if not shown), reference.""",
}

BASE_RULES = """
STRICT OUTPUT RULES:
1. Return ONLY valid JSON - no markdown, no code blocks, no explanation text before or after
2. Extract EVERY row - never truncate or summarise, never say "and X more rows"
3. All numeric values must be clean floats (no currency symbols, commas, spaces - just digits and decimal point)
4. Dates in YYYY-MM-DD format where possible; preserve original format if ambiguous
5. Never invent data - only extract what is visibly present in the document
6. If a field is not visible, use empty string "" for text fields and 0 for numeric fields

Return this exact structure:
{
  "document_type": "invoice|bank_statement|receipt|table|other",
  "rows": [
    { "date": "", "description": "", "amount": 0.0, "type": "", "category": "", "gst": 0.0, "reference": "" }
  ],
  "summary": { "total_rows": 0, "total_amount": 0.0, "currency": "INR" },
  "confidence": 0.0
}
"""

VALIDATION_PROMPT = """You are a data quality auditor. You will receive an extracted JSON and must verify and correct it.

Check ALL of the following and fix any issues:
1. Row count: are ALL rows from the original document present? If rows are missing, add them.
2. Amounts: are all amount and gst values clean floats? Fix any that are strings, null, or contain symbols.
3. Dates: normalize all dates to YYYY-MM-DD where the original date is unambiguous. If the date is unclear, keep original.
4. Duplicates: remove exact duplicate rows (same date + description + amount).
5. Types: every row must have type set to one of: debit, credit, expense, income. Infer from context if empty.
6. Confidence: set the top-level "confidence" field (0.0-1.0) based on how clearly the document data was visible and how complete the extraction is.

Return ONLY the corrected JSON object. No explanation. No markdown.
"""


# -- Helpers --

def clean_number(val):
    if isinstance(val, (int, float)):
        return float(val)
    cleaned = re.sub(r'[^\d.]', '', str(val))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def normalize_date(val):
    if not val or str(val).strip() == '':
        return ''
    try:
        from dateutil import parser as dateparser
        return dateparser.parse(str(val)).strftime('%Y-%m-%d')
    except Exception:
        return str(val)


def deduplicate_rows(rows):
    seen = set()
    result = []
    for row in rows:
        key = (row.get('date', ''), row.get('description', ''), row.get('amount', 0))
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result


def post_process(result):
    rows = result.get('rows', [])
    cleaned = []
    for row in rows:
        row['amount'] = clean_number(row.get('amount', 0))
        row['gst'] = clean_number(row.get('gst', 0))
        row['date'] = normalize_date(row.get('date', ''))
        if not row.get('type'):
            row['type'] = 'debit'
        cleaned.append(row)
    cleaned = deduplicate_rows(cleaned)
    total = sum(r['amount'] for r in cleaned)
    result['rows'] = cleaned
    result['summary'] = {
        'total_rows': len(cleaned),
        'total_amount': round(total, 2),
        'currency': result.get('summary', {}).get('currency', 'INR'),
    }
    return result


def parse_json_response(response):
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    brace_start = response.find('{')
    brace_end = response.rfind('}')
    if brace_start != -1 and brace_end != -1:
        try:
            return json.loads(response[brace_start:brace_end + 1])
        except json.JSONDecodeError:
            pass
    return None


# -- Pass 1: Detect document type --

async def detect_type(image_base64_or_text, is_image=True):
    prompt = "What type of financial document is this? Reply with EXACTLY one of these words only: invoice, bank_statement, receipt, table, other"
    
    if is_image:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64_or_text}"
                        }
                    }
                ]
            }
        ]
    else:
        messages = [
            {
                "role": "user",
                "content": f"{prompt}\n\nDocument text:\n{image_base64_or_text[:3000]}"
            }
        ]
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=10,
        temperature=0
    )
    
    detected = response.choices[0].message.content.strip().lower().replace(' ', '_')
    if detected not in TYPE_PROMPTS:
        detected = 'other'
    return detected


# -- Pass 2: Type-specific extraction --

async def extract_pass(image_base64_or_text, doc_type, user_requirements, is_image=True):
    type_prompt = TYPE_PROMPTS.get(doc_type, TYPE_PROMPTS['other'])
    req_section = f"\nUSER REQUIREMENTS: {user_requirements}\nPrioritize extracting fields that match these requirements.\n" if user_requirements and user_requirements.strip() else ""
    system_message = f"{type_prompt}{req_section}\n{BASE_RULES}"

    prompt = "Extract ALL structured data from this document. Return ONLY valid JSON."
    
    if is_image:
        messages = [
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64_or_text}"
                        }
                    }
                ]
            }
        ]
    else:
        messages = [
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": f"{prompt}\n\nDocument:\n{image_base64_or_text[:15000]}"
            }
        ]

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=4000,
        temperature=0
    )
    
    return parse_json_response(response.choices[0].message.content)


# -- Pass 3: Validate + self-correct --

async def validate_pass(extracted_json, image_base64_or_text, is_image=True):
    extracted_str = json.dumps(extracted_json, indent=2)
    prompt = f"Here is the extracted JSON:\n{extracted_str}\n\nNow compare against the original document and return the corrected JSON only."

    if is_image:
        messages = [
            {"role": "system", "content": VALIDATION_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64_or_text}"
                        }
                    }
                ]
            }
        ]
    else:
        messages = [
            {"role": "system", "content": VALIDATION_PROMPT},
            {"role": "user", "content": prompt}
        ]

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=4000,
        temperature=0
    )
    
    corrected = parse_json_response(response.choices[0].message.content)
    return corrected if corrected else extracted_json


# -- Image loader --

def load_image_base64(file_path):
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


# -- Main pipeline for images --

async def process_image(file_path, user_requirements):
    img_base64 = load_image_base64(file_path)

    # Pass 1: detect
    doc_type = await detect_type(img_base64, is_image=True)

    # Pass 2: extract
    result = await extract_pass(img_base64, doc_type, user_requirements, is_image=True)
    if not result or not isinstance(result.get('rows'), list):
        return {"error": "Failed to extract structured data from this image. Please try a clearer photo."}
    result['document_type'] = doc_type

    # Pass 3: validate
    result = await validate_pass(result, img_base64, is_image=True)

    return post_process(result)


# -- Main pipeline for PDF text --

async def process_text(text, user_requirements):
    # Pass 1: detect
    doc_type = await detect_type(text, is_image=False)

    # Pass 2: extract
    result = await extract_pass(text, doc_type, user_requirements, is_image=False)
    if not result or not isinstance(result.get('rows'), list):
        return {"error": "Failed to extract structured data. Please try uploading an image of the document."}
    result['document_type'] = doc_type

    # Pass 3: validate (text-only, no image in validate pass)
    result = await validate_pass(result, text, is_image=False)

    return post_process(result)


# -- PDF handler --

async def process_pdf(file_path, user_requirements):
    # Try text extraction first
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if len(text.strip()) > 100:
            return await process_text(text, user_requirements)
    except Exception as e:
        print(f"PDF text extraction failed: {e}", file=sys.stderr)

    # Fallback: convert all pages to images and merge results
    try:
        import pdfplumber
        import io
        all_rows = []
        doc_type = 'other'
        currency = 'INR'

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages[:5]):  # max 5 pages
                try:
                    img = page.to_image(resolution=200)
                    img_bytes = io.BytesIO()
                    img.original.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    temp_img = file_path + f'_p{page_num}.png'
                    with open(temp_img, 'wb') as f:
                        f.write(img_bytes.getvalue())
                    page_result = await process_image(temp_img, user_requirements)
                    os.remove(temp_img)
                    if page_result and 'rows' in page_result:
                        all_rows.extend(page_result['rows'])
                        if page_num == 0:
                            doc_type = page_result.get('document_type', 'other')
                            currency = page_result.get('summary', {}).get('currency', 'INR')
                except Exception as pe:
                    print(f"Page {page_num} failed: {pe}", file=sys.stderr)
                    continue

        if all_rows:
            merged = {
                'document_type': doc_type,
                'rows': all_rows,
                'summary': {'total_rows': len(all_rows), 'total_amount': 0, 'currency': currency},
                'confidence': 0.8,
            }
            return post_process(merged)
    except Exception as e:
        print(f"PDF image fallback failed: {e}", file=sys.stderr)

    return {"error": "Could not extract data from this PDF. Please upload a clearer PDF or an image of the document."}


# -- Entry point --

async def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No file path provided"}))
        sys.exit(1)

    file_path = sys.argv[1]
    user_requirements = sys.argv[2] if len(sys.argv) > 2 else ""

    if not os.path.exists(file_path):
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)

    ext = Path(file_path).suffix.lower()

    try:
        if ext in ['.jpg', '.jpeg', '.png', '.webp']:
            result = await process_image(file_path, user_requirements)
        elif ext == '.pdf':
            result = await process_pdf(file_path, user_requirements)
        else:
            result = {"error": f"Unsupported file type: {ext}"}

        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
