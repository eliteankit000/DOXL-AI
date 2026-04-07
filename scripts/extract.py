#!/usr/bin/env python3
"""
DocXL AI — Fast Document Extraction Engine v6.1
OPTIMIZED FOR SPEED: 5-10 second processing with layout awareness
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

# ═══════════════════════════════════════════════════════════════════
# FAST EXTRACTION PROMPT (Optimized for Speed)
# ═══════════════════════════════════════════════════════════════════

FAST_EXTRACTION_PROMPT = """You are a high-performance AI document processing engine optimized for SPEED and EFFICIENCY.

Your task is to extract and structure data from documents within seconds while maintaining high accuracy.

---

# 🎯 PRIMARY GOAL

✔ Fast processing
✔ Clean structured output
✔ Excel-ready format

---

# 🧠 STEP 1: FAST DOCUMENT CLASSIFICATION

Quickly classify into:
- bank_statement (has Date, Description, Debit/Credit, Balance)
- invoice (has line items, invoice number, totals)
- form (key-value pairs, application forms)
- table (generic structured data)
- receipt (short transaction summary)
- mixed (multiple sections)

---

# ⚡ STEP 2: EXTRACT ESSENTIAL DATA

**IF bank statement:**
→ Extract transaction table with: Date, Description, Debit, Credit, Balance

**IF invoice:**
→ Extract:
  - Invoice metadata (Invoice No, Date, Customer)
  - Line items table (Item, Quantity, Price, Amount)
  - Totals (Subtotal, Tax, Grand Total)

**IF form:**
→ Extract all key-value pairs as columns

**IF table:**
→ Extract table with headers and rows

---

# 🚀 STEP 3: OUTPUT FORMAT (STRICT)

Return ONLY JSON:

```json
{
  "document_type": "bank_statement|invoice|form|table|receipt|mixed",
  "columns": ["Column1", "Column2", "Column3"],
  "rows": [
    {"Column1": "value", "Column2": "value", "Column3": "value"}
  ],
  "confidence": 0.95
}
```

---

# ⚠️ CRITICAL RULES

1. **ALWAYS return columns + rows** — NEVER return empty arrays
2. **Clean column names** — Title Case, no special characters
3. **One row per record** — Each transaction/item = one row
4. **Remove currency symbols** — Keep only numbers (₹, $, Rs. → remove)
5. **Date format** — DD/MM/YYYY
6. **Numbers only** — No commas in numeric values
7. **All visible data** — Don't skip any rows from tables

---

# 🧠 EXAMPLES

**Example 1: Bank Statement**
```json
{
  "document_type": "bank_statement",
  "columns": ["Date", "Description", "Debit", "Credit", "Balance"],
  "rows": [
    {"Date": "15/01/2024", "Description": "ATM Withdrawal", "Debit": "5000", "Credit": "", "Balance": "45000"}
  ],
  "confidence": 0.95
}
```

**Example 2: Invoice**
```json
{
  "document_type": "invoice",
  "columns": ["Invoice No", "Date", "Item", "Quantity", "Price", "Amount", "Tax", "Total"],
  "rows": [
    {"Invoice No": "43", "Date": "06/04/2026", "Item": "Room Tariff", "Quantity": "1", "Price": "1619.05", "Amount": "1619.05", "Tax": "80.95", "Total": "1700"}
  ],
  "confidence": 0.92
}
```

**Example 3: Form**
```json
{
  "document_type": "form",
  "columns": ["Name", "Email", "Phone", "Address"],
  "rows": [
    {"Name": "John Doe", "Email": "john@email.com", "Phone": "9876543210", "Address": "123 Main St"}
  ],
  "confidence": 0.88
}
```

---

# 🎯 FINAL REMINDER

- Return ONLY the JSON object
- NO text before or after
- NO markdown blocks
- NO explanations
- Ensure columns and rows are NEVER empty

Return the JSON now:"""

# ═══════════════════════════════════════════════════════════════════
# SINGLE-PASS FAST EXTRACTION
# ═══════════════════════════════════════════════════════════════════

async def extract_from_image(image_base64: str, user_requirements: str = "") -> dict:
    """
    Fast single-pass extraction optimized for speed.
    Target: 5-10 seconds per page.
    """
    log_step("EXTRACTION", "Starting fast extraction")
    
    prompt = FAST_EXTRACTION_PROMPT
    if user_requirements:
        prompt += f"\n\n**USER REQUIREMENTS:** {user_requirements}\nPay special attention to these requirements."
    
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
                                "url": f"data:image/png;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=8192,
            temperature=0.1
        )
        
        raw_output = response.choices[0].message.content.strip()
        log_step("EXTRACTION", f"GPT-4o response received ({len(raw_output)} chars)")
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if not json_match:
            log_step("EXTRACTION_ERROR", "No JSON found in response")
            raise ValueError("No JSON found in GPT-4o response")
        
        result = json.loads(json_match.group())
        
        # Validate required fields
        if 'columns' not in result or 'rows' not in result:
            log_step("EXTRACTION_ERROR", "Missing columns or rows in response")
            raise ValueError("Invalid format: missing columns or rows")
        
        if not result['columns'] or not result['rows']:
            log_step("EXTRACTION_WARNING", "Empty columns or rows - retrying with fallback")
            # Fallback: try to extract ANY data
            return await extract_with_fallback(image_base64, user_requirements)
        
        # Add confidence if missing
        if 'confidence' not in result:
            result['confidence'] = 0.85
        
        # Add document_type if missing
        if 'document_type' not in result:
            result['document_type'] = 'table'
        
        log_step("EXTRACTION_SUCCESS", f"Extracted {len(result['rows'])} rows, {len(result['columns'])} columns")
        return result
    
    except Exception as e:
        log_step("EXTRACTION_ERROR", f"Extraction failed: {e}")
        # Return fallback structure
        return await extract_with_fallback(image_base64, user_requirements)

async def extract_with_fallback(image_base64: str, user_requirements: str = "") -> dict:
    """
    Fallback extraction with simplified prompt.
    """
    log_step("FALLBACK", "Attempting fallback extraction")
    
    fallback_prompt = """Extract ALL data from this document into a table format.

Return ONLY JSON:
{
  "document_type": "table",
  "columns": ["Column1", "Column2"],
  "rows": [{"Column1": "value", "Column2": "value"}],
  "confidence": 0.75
}

CRITICAL: columns and rows must NEVER be empty. Extract at least something from the document."""
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": fallback_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4096,
            temperature=0.2
        )
        
        raw_output = response.choices[0].message.content.strip()
        json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        
        if json_match:
            result = json.loads(json_match.group())
            if result.get('columns') and result.get('rows'):
                log_step("FALLBACK_SUCCESS", f"Fallback extracted {len(result['rows'])} rows")
                return result
    except Exception as e:
        log_step("FALLBACK_ERROR", f"Fallback failed: {e}")
    
    # Ultimate fallback: return minimal structure
    return {
        "document_type": "unknown",
        "columns": ["Content"],
        "rows": [{"Content": "Extraction failed - please try a clearer image"}],
        "confidence": 0.0
    }

# ═══════════════════════════════════════════════════════════════════
# MULTI-PAGE HANDLING
# ═══════════════════════════════════════════════════════════════════

async def process_pdf_pages(file_path: str, user_requirements: str = "") -> dict:
    """
    Process multi-page PDF by extracting pages and combining results.
    """
    log_step("PDF_PROCESSING", f"Processing PDF: {file_path}")
    
    try:
        import pdfplumber
        from PIL import Image
        import io
        
        pages_data = []
        
        with pdfplumber.open(file_path) as pdf:
            total_pages = min(len(pdf.pages), 10)  # Max 10 pages
            log_step("PDF_PROCESSING", f"PDF has {total_pages} page(s)")
            
            for i in range(total_pages):
                page = pdf.pages[i]
                
                # Convert page to image
                pil_image = page.to_image(resolution=150).original
                buffer = io.BytesIO()
                pil_image.save(buffer, format='PNG')
                img_bytes = buffer.getvalue()
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                
                # Extract from this page
                page_result = await extract_from_image(img_base64, user_requirements)
                pages_data.append(page_result)
                
                log_step("PDF_PROCESSING", f"Page {i+1}/{total_pages} processed: {len(page_result.get('rows', []))} rows")
        
        # Combine results from all pages
        if len(pages_data) == 1:
            return pages_data[0]
        else:
            # Multi-page: combine rows from all pages
            combined = {
                "document_type": pages_data[0].get('document_type', 'table'),
                "columns": pages_data[0].get('columns', []),
                "rows": [],
                "confidence": sum(p.get('confidence', 0.85) for p in pages_data) / len(pages_data),
                "pages": len(pages_data)
            }
            
            for page_data in pages_data:
                combined['rows'].extend(page_data.get('rows', []))
            
            log_step("PDF_PROCESSING", f"Combined {len(combined['rows'])} rows from {len(pages_data)} pages")
            return combined
    
    except Exception as e:
        log_step("PDF_PROCESSING_ERROR", f"PDF processing failed: {e}")
        # Fallback: treat as image
        with open(file_path, 'rb') as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')
            return await extract_from_image(img_base64, user_requirements)

async def process_image(file_path: str, user_requirements: str = "") -> dict:
    """
    Process single image file.
    """
    log_step("IMAGE_PROCESSING", f"Processing image: {file_path}")
    
    with open(file_path, 'rb') as f:
        img_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    return await extract_from_image(img_base64, user_requirements)

# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
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
    
    file_ext = Path(file_path).suffix.lower()
    
    try:
        start_time = time.time()
        
        if file_ext == '.pdf':
            result = await process_pdf_pages(file_path, user_requirements)
        else:
            result = await process_image(file_path, user_requirements)
        
        elapsed = time.time() - start_time
        log_step("COMPLETE", f"Processing completed in {elapsed:.2f}s")
        
        # Ensure result has required fields
        if 'columns' not in result:
            result['columns'] = []
        if 'rows' not in result:
            result['rows'] = []
        if 'confidence' not in result:
            result['confidence'] = 0.85
        if 'document_type' not in result:
            result['document_type'] = 'table'
        
        print(json.dumps(result, indent=2))
    
    except Exception as e:
        log_step("FATAL_ERROR", str(e))
        print(json.dumps({
            "error": str(e),
            "document_type": "unknown",
            "columns": [],
            "rows": [],
            "confidence": 0.0
        }))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
