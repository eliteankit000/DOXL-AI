#!/usr/bin/env python3
"""
DocXL AI — FastAPI Production Backend
Two-engine architecture: Core (fast) + AI (async)
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from pathlib import Path
import asyncio

# Import engines
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from pdf_engine.universal_pipeline import process_document_universal
from pdf_engine.exporter import export_to_excel_buffer
from pdf_engine.ai_engine import enhance_document

app = FastAPI(
    title="DocXL AI - Production PDF/Image to Excel API",
    version="8.0",
    description="Fast deterministic document processing with optional AI enhancement"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache for async AI results
ai_results_cache = {}

# ═══════════════════════════════════════════════════════════════════
# ENGINE 1: CORE PROCESSING (FAST, DETERMINISTIC)
# ═══════════════════════════════════════════════════════════════════

@app.post("/process-pdf", summary="Fast PDF/Image to Excel (Core Engine)")
async def process_pdf_endpoint(file: UploadFile = File(...)):
    """
    **CORE ENGINE - FAST PROCESSING**
    
    - Accepts PDF or Image (JPG/PNG)
    - Uses PyMuPDF for PDFs, PaddleOCR for images
    - Returns Excel file in <2 seconds
    - NO AI/LLM calls in pipeline
    - Deterministic algorithmic approach
    
    Returns:
        Excel file (.xlsx)
    """
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in ['.pdf', '.jpg', '.jpeg', '.png', '.bmp']:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Supported: PDF, JPG, PNG"
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Process with CORE ENGINE (fast, no LLM)
        result = process_document_universal(tmp_path)
        
        if 'error' in result:
            raise HTTPException(status_code=422, detail=result['error'])
        
        # Generate Excel
        excel_bytes = export_to_excel_buffer({
            'headers': result['columns'],
            'rows': result['rows']
        })
        
        if not excel_bytes:
            raise HTTPException(status_code=422, detail="Excel generation failed")
        
        # Return Excel file
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=docxl_export_{int(asyncio.get_event_loop().time())}.xlsx"
            }
        )
    
    finally:
        # Cleanup temp file
        try:
            os.unlink(tmp_path)
        except:
            pass


@app.post("/process-json", summary="Fast Processing (Returns JSON)")
async def process_json_endpoint(file: UploadFile = File(...)):
    """
    **CORE ENGINE - Returns JSON instead of Excel**
    
    Useful for:
    - API integration
    - Testing
    - Data preview
    
    Returns:
        {
            'columns': List[str],
            'rows': List[Dict],
            'processing_time': float,
            'extraction_method': str
        }
    """
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in ['.pdf', '.jpg', '.jpeg', '.png', '.bmp']:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type"
        )
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        result = process_document_universal(tmp_path)
        return JSONResponse(content=result)
    
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass


# ═══════════════════════════════════════════════════════════════════
# ENGINE 2: AI ENHANCEMENT (ASYNC, OPTIONAL)
# ═══════════════════════════════════════════════════════════════════

async def run_ai_enhancement_background(document_id: str, table_data: dict):
    """
    Background task for AI enhancement.
    """
    print(f"[AI_ENGINE] Starting enhancement for {document_id}")
    
    try:
        enhancements = await enhance_document(table_data)
        ai_results_cache[document_id] = enhancements
        print(f"[AI_ENGINE] Complete for {document_id}")
    except Exception as e:
        print(f"[AI_ENGINE] Error: {e}")
        ai_results_cache[document_id] = {"error": str(e)}


@app.post("/enhance", summary="AI Enhancement (Async)")
async def enhance_endpoint(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    **AI ENGINE - ASYNC ENHANCEMENT**
    
    Two-step process:
    1. Returns Excel immediately (from core engine)
    2. Runs AI enhancement in background
    3. Fetch AI results with GET /enhancements/{document_id}
    
    Returns:
        {
            'excel_url': str,
            'document_id': str,
            'status': 'processing'
        }
    """
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in ['.pdf', '.jpg', '.jpeg', '.png', '.bmp']:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # STEP 1: Fast core processing
        result = process_document_universal(tmp_path)
        
        if 'error' in result:
            raise HTTPException(status_code=422, detail=result['error'])
        
        # Generate document ID
        import uuid
        document_id = str(uuid.uuid4())
        
        # STEP 2: Queue AI enhancement (background)
        table_data = {
            'headers': result['columns'],
            'rows': result['rows'],
            'document_type': result['document_type']
        }
        
        if background_tasks:
            background_tasks.add_task(
                run_ai_enhancement_background,
                document_id,
                table_data
            )
        
        return JSONResponse(content={
            'document_id': document_id,
            'status': 'processing',
            'message': 'Excel generated. AI enhancement in progress.',
            'data': result
        })
    
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass


@app.get("/enhancements/{document_id}", summary="Get AI Enhancement Results")
async def get_enhancements(document_id: str):
    """
    Fetch AI enhancement results by document ID.
    
    Returns:
        {
            'summary': str,
            'invoice_fields': dict,
            'insights': list
        }
    """
    if document_id not in ai_results_cache:
        return JSONResponse(
            status_code=202,
            content={'status': 'pending', 'message': 'AI processing in progress'}
        )
    
    return JSONResponse(content={
        'status': 'complete',
        'enhancements': ai_results_cache[document_id]
    })


# ═══════════════════════════════════════════════════════════════════
# HEALTH & INFO ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.get("/health", summary="Health Check")
async def health_check():
    """
    API health check.
    """
    return {
        "status": "ok",
        "service": "DocXL AI FastAPI",
        "version": "8.0",
        "engines": {
            "core": "PyMuPDF + Algorithmic",
            "ai": "OpenAI (async)"
        }
    }


@app.get("/", summary="API Info")
async def root():
    """
    API information and available endpoints.
    """
    return {
        "service": "DocXL AI - Production PDF/Image to Excel API",
        "version": "8.0",
        "endpoints": {
            "POST /process-pdf": "Fast Excel generation (Core Engine)",
            "POST /process-json": "Fast JSON output (Core Engine)",
            "POST /enhance": "Excel + AI enhancement (Async)",
            "GET /enhancements/{id}": "Fetch AI results",
            "GET /health": "Health check"
        },
        "features": {
            "supported_formats": ["PDF", "JPG", "PNG"],
            "processing_speed": "<2 seconds per page",
            "core_engine": "Deterministic (no LLM)",
            "ai_engine": "Optional async enhancement"
        }
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
