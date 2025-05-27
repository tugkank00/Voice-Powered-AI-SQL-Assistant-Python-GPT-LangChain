from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
import os
import json
import io
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime, timezone
import time

from app.services.base.protocols import (
    TextToSqlProtocol,
    SqlExecutorProtocol,
    QueryProcessorProtocol,
    VoiceToTextProtocol,
    ReportGeneratorProtocol,
)
from app.utils.dependencies import (
    get_sql_query_service,
    get_voice_to_text_service,
    get_report_service,
)
from app.utils.sanitize import sanitize_rows
from app.utils.pdf_utils import (
    validate_rows_json,
    parse_headers,
    create_query_result,
    generate_pdf_response,
)
from app.models.query_result import QueryResult  
from fastapi.exceptions import RequestValidationError
from app.exceptions.base import BaseAppException
from app.models.api_responses import add_common_responses, COMMON_RESPONSES
from app.middleware.exception_handler import (
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    unexpected_exception_handler,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI SQL Assistant API",
    description="API for natural language to SQL conversion with voice support",
    version="1.0.0",
    responses=COMMON_RESPONSES
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.add_exception_handler(BaseAppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unexpected_exception_handler)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post(
    "/ask", 
    response_class=HTMLResponse,
    summary="Ask a question in natural language",
    description="Convert natural language question to SQL, execute it, and return results",
    responses={
        200: {"description": "Success - Question processed and results returned"},
        **COMMON_RESPONSES
    },
    tags=["Query Processing"]
)
async def ask(
    request: Request,
    question: str = Form(..., description="Natural language question about the data"),
    sql_query_service: QueryProcessorProtocol = Depends(get_sql_query_service),
):
    logger.info(f"Received question: {question}")
    if not question or question.strip() == "":
        from app.exceptions.domain import EmptyQuestionException
        raise EmptyQuestionException()
    result = sql_query_service.process_question(question)
    
    sanitized = sanitize_rows(result.rows, headers=result.headers)
    context = {
        "request": request,
        "question": question,
        "sql": result.sql,
        "execution_time": result.execution_time_ms,
        "headers": result.headers,
        "rows": sanitized,
        "error": result.error,
    }
    return templates.TemplateResponse(request, "index.html", context)


@app.post(
    "/ask-voice", 
    response_class=HTMLResponse,
    summary="Ask a question via voice input",
    description="Upload audio file, transcribe to text, convert to SQL, and return results",
    responses={
        200: {"description": "Success - Voice processed and results returned"},
        **COMMON_RESPONSES
    },
    tags=["Voice"]
)
async def ask_voice(
    request: Request,
    file: UploadFile = File(..., description="Audio file (mp3, mp4, mpeg, mpga, m4a, wav, webm)"),
    sql_query_service: QueryProcessorProtocol = Depends(get_sql_query_service),
    voice_to_text_service: VoiceToTextProtocol = Depends(get_voice_to_text_service),
):

    if not file.filename:
        from app.exceptions.domain import InvalidFileFormatException
        raise InvalidFileFormatException(details={"reason": "No filename provided"})
    
    file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if file_ext not in ['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm']:
        from app.exceptions.domain import InvalidFileFormatException
        raise InvalidFileFormatException(file_type=file_ext)

    file_content = await file.read()
    if len(file_content) == 0:
        from app.exceptions.domain import InvalidFileFormatException
        raise InvalidFileFormatException(
            details={"reason": "Empty file", "file_size": 0}
        )

    import uuid
    tmp_path = f"/tmp/{uuid.uuid4().hex}_{file.filename}"
    try:
        with open(tmp_path, "wb") as buf:
            buf.write(file_content)
        
        question = voice_to_text_service.transcribe(tmp_path)
        logger.info(f"Voice transcription: {question}")
        
        result = sql_query_service.process_question(question)
        
        sanitized = sanitize_rows(result.rows, headers=result.headers)
        context = {
            "request": request,
            "question": question,
            "sql": result.sql,
            "execution_time": result.execution_time_ms,
            "headers": result.headers,
            "rows": sanitized,
            "error": result.error,
        }
        return templates.TemplateResponse("index.html", context)
        
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {tmp_path}: {e}")

@app.post(
    "/download-report-pdf",
    summary="Generate PDF report",
    description="Generate and download PDF report based on query results",
    responses={
        200: {
            "description": "Success - PDF report generated",
            "content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}}
        },
        **COMMON_RESPONSES
    },
    tags=["Reports"]
)
async def download_report_pdf(
    rows_json: str = Form(..., description="JSON string containing query result rows"),
    headers_json: str = Form(None, description="JSON string containing table headers"),
    question: str = Form(..., description="Original question that generated the results"),
    sql: str = Form(None, description="SQL query that was executed"),
    report_service: ReportGeneratorProtocol = Depends(get_report_service),
):
    
    logger.info(f"PDF request - Question: {question}")

    try:
        rows_data = validate_rows_json(rows_json, logger)
        headers = parse_headers(headers_json, rows_data, logger)
    except Exception as e:
        from app.exceptions.domain import InvalidRequestDataException
        raise InvalidRequestDataException(
            field_name="rows_json" if "rows" in str(e).lower() else "headers_json",
            reason=f"Invalid JSON format: {str(e)}",
            original_exception=e
        )
    
    logger.info(f"Processing PDF with {len(rows_data)} rows")
    
    qr = create_query_result(question, sql, headers, rows_data)
    
    pdf_bytes = report_service.generate_pdf(qr)
    
    return generate_pdf_response(pdf_bytes, question, logger)


@app.get(
    "/health",
    summary="Health check",
    description="Check API health status",
    responses={
        200: {"description": "API is healthy"},
        503: {"description": "API is unhealthy"}
    },
    tags=["Health"]
)
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        from app.exceptions.domain import InternalServerException
        raise InternalServerException(
            message="Health check failed",
            details={"error": str(e)}
        )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    logger.info(
        f"Request: {request.method} {request.url}",
        extra={
            "method": request.method,
            "url": str(request.url),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "ip": request.client.host if request.client else "unknown"
        }
    )

    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"Response: {response.status_code} in {process_time:.3f}s",
        extra={
            "status_code": response.status_code,
            "process_time": process_time,
            "method": request.method,
            "url": str(request.url)
        }
    )
    
    return response