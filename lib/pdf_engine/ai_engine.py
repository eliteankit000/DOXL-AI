"""
DocXL AI - AI Enhancement Engine (Optional, Async)
Adds intelligence AFTER core processing

IMPORTANT: This runs ASYNCHRONOUSLY and does NOT block Excel generation
"""
import os
from typing import Dict, List
from openai import AsyncOpenAI

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

async def generate_document_summary(table_data: Dict) -> str:
    """
    Generate AI summary of extracted document.
    
    Args:
        table_data: {headers, rows, document_type}
        
    Returns:
        Natural language summary
    """
    if not OPENAI_API_KEY:
        return "AI summarization not available (no API key)"
    
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])
        doc_type = table_data.get('document_type', 'table')
        
        # Create prompt
        prompt = f"""Analyze this {doc_type} and provide a brief summary.

Headers: {', '.join(headers)}
Row count: {len(rows)}
Sample data (first 3 rows): {rows[:3]}

Generate a 2-3 sentence summary."""
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Faster model for summaries
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"Summary generation failed: {e}"


async def label_invoice_fields(table_data: Dict) -> Dict[str, str]:
    """
    Identify key invoice fields using AI.
    
    Returns:
        {
            'invoice_number': '...',
            'invoice_date': '...',
            'total_amount': '...',
            'customer_name': '...'
        }
    """
    if not OPENAI_API_KEY:
        return {}
    
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        rows = table_data.get('rows', [])
        
        # Create prompt
        prompt = f"""Extract key invoice fields from this data:

Data: {rows[:10]}  # First 10 rows

Return ONLY JSON:
{{
  "invoice_number": "...",
  "invoice_date": "...",
  "total_amount": "...",
  "customer_name": "..."
}}

If field not found, use empty string."""
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        return {"error": str(e)}


async def enhance_document(table_data: Dict) -> Dict:
    """
    Main AI enhancement pipeline.
    
    Runs asynchronously AFTER core processing.
    
    Returns:
        {
            'summary': str,
            'invoice_fields': dict,
            'insights': list
        }
    """
    print("[AI_ENGINE] Starting async enhancement...")
    
    # Run enhancements in parallel
    import asyncio
    
    summary_task = generate_document_summary(table_data)
    fields_task = label_invoice_fields(table_data)
    
    summary, fields = await asyncio.gather(summary_task, fields_task)
    
    return {
        'summary': summary,
        'invoice_fields': fields,
        'insights': []  # Placeholder for additional insights
    }
