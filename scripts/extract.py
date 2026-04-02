#!/usr/bin/env python3
"""
DocXL AI - Document Extraction Script
Uses emergentintegrations library to extract structured data from documents.
"""
import sys
import os
import json
import base64
import asyncio
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, '/app')

from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', 'sk-emergent-8124e477260C6Fa4cE')

EXTRACTION_PROMPT = """You are a financial document data extraction AI. Extract ALL structured data from this document.

IMPORTANT RULES:
1. Return ONLY valid JSON - no markdown, no code blocks, no explanation
2. Extract EVERY row of data visible in the document
3. Numeric values must be clean numbers (no currency symbols, no commas)
4. Dates should be in YYYY-MM-DD format when possible
5. Do NOT hallucinate or invent data - only extract what is visible
6. Preserve the exact number of rows from the document

Return this exact JSON structure:
{
  "document_type": "invoice" | "bank_statement" | "receipt" | "table" | "other",
  "rows": [
    {
      "date": "YYYY-MM-DD or original format",
      "description": "transaction/item description",
      "amount": 0.00,
      "type": "debit" | "credit" | "expense" | "income",
      "category": "category if identifiable",
      "gst": 0.00,
      "reference": "reference number if available"
    }
  ],
  "summary": {
    "total_rows": 0,
    "total_amount": 0.00,
    "currency": "INR" | "USD" | "EUR" | "detected currency"
  }
}

If the document is an invoice, extract line items. If it's a bank statement, extract transactions. If it's a table/image, extract all visible rows.
"""

async def extract_from_image(file_path: str) -> dict:
    """Extract data from an image file using Vision API."""
    with open(file_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"extract-{os.path.basename(file_path)}",
        system_message=EXTRACTION_PROMPT
    )
    chat.with_model("openai", "gpt-4o")
    
    image_content = ImageContent(image_base64=image_data)
    user_message = UserMessage(
        text="Extract all structured financial data from this document image. Return ONLY valid JSON.",
        file_contents=[image_content]
    )
    
    response = await chat.send_message(user_message)
    return parse_response(response)

async def extract_from_pdf_text(text: str) -> dict:
    """Extract data from PDF text using LLM."""
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"extract-pdf-text",
        system_message=EXTRACTION_PROMPT
    )
    chat.with_model("openai", "gpt-4o")
    
    user_message = UserMessage(
        text=f"Extract all structured financial data from this document text. Return ONLY valid JSON.\n\nDocument text:\n{text[:15000]}"
    )
    
    response = await chat.send_message(user_message)
    return parse_response(response)

async def extract_from_pdf(file_path: str) -> dict:
    """Extract data from a PDF file."""
    # Try text extraction first
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        if len(text.strip()) > 50:
            # PDF has extractable text
            return await extract_from_pdf_text(text)
    except Exception as e:
        print(f"PDF text extraction failed: {e}", file=sys.stderr)
    
    # If text extraction fails, try converting first page to image
    try:
        import pdfplumber
        from PIL import Image
        import io
        
        with pdfplumber.open(file_path) as pdf:
            if pdf.pages:
                page = pdf.pages[0]
                img = page.to_image(resolution=200)
                img_bytes = io.BytesIO()
                img.original.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # Save temp image
                temp_path = file_path + '.png'
                with open(temp_path, 'wb') as f:
                    f.write(img_bytes.getvalue())
                
                result = await extract_from_image(temp_path)
                os.remove(temp_path)
                return result
    except Exception as e:
        print(f"PDF to image conversion failed: {e}", file=sys.stderr)
    
    return {"error": "Could not extract data from this PDF. Please try uploading a clearer document or an image."}

def parse_response(response: str) -> dict:
    """Parse the LLM response into a JSON object."""
    # Try direct JSON parse
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Try extracting JSON from markdown code blocks
    import re
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try finding JSON object in the response
    brace_start = response.find('{')
    brace_end = response.rfind('}')
    if brace_start != -1 and brace_end != -1:
        try:
            return json.loads(response[brace_start:brace_end + 1])
        except json.JSONDecodeError:
            pass
    
    return {"error": "Failed to parse AI response", "raw_response": response[:500]}

async def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No file path provided"}))
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)
    
    ext = Path(file_path).suffix.lower()
    
    try:
        if ext in ['.jpg', '.jpeg', '.png', '.webp']:
            result = await extract_from_image(file_path)
        elif ext == '.pdf':
            result = await extract_from_pdf(file_path)
        else:
            result = {"error": f"Unsupported file type: {ext}"}
        
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
