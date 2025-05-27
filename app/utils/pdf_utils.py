import json
import io
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from app.models.query_result import QueryResult

def validate_rows_json(rows_json: str, logger) -> List[Dict[str, Any]]:
    if not rows_json or rows_json.strip() == "":
        logger.error("Empty rows_json received")
        raise HTTPException(status_code=400, detail="No data provided for PDF generation")
    
    try:
        rows_data = json.loads(rows_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid rows_json: {e}")
        logger.error(f"Received rows_json: {rows_json[:200]}...")
        raise HTTPException(status_code=400, detail=f"Invalid JSON in rows_json: {str(e)}")
    
    if not rows_data:
        raise HTTPException(status_code=400, detail="No data rows provided")
    
    return rows_data

def parse_headers(headers_json: Optional[str], rows_data: List[Dict[str, Any]], logger) -> List[str]:

    headers = []
    if headers_json:
        try:
            headers = json.loads(headers_json)
        except json.JSONDecodeError:
            logger.warning("Invalid headers_json, extracting from rows")
            headers = list(rows_data[0].keys()) if rows_data else []
    else:
        headers = list(rows_data[0].keys()) if rows_data else []
    
    if not headers:
        raise HTTPException(status_code=400, detail="No headers found")
    
    return headers

def create_query_result(
    question: str,
    sql: Optional[str],
    headers: List[str],
    rows_data: List[Dict[str, Any]]
) -> QueryResult:
    return QueryResult(
        question=question or "Database Query",
        sql=sql or "-- SQL not provided",
        headers=headers,
        rows=[tuple(row.get(h, '') for h in headers) for row in rows_data],
        execution_time_ms=0,
        error=None
    )

def generate_pdf_response(pdf_bytes: bytes, question: str, logger) -> StreamingResponse:
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="PDF generation returned empty result")
    
    logger.info(f"PDF generated successfully, size: {len(pdf_bytes)} bytes")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="report_{question[:30].replace(" ", "_")}.pdf"',
            "Content-Length": str(len(pdf_bytes))
        }
    )