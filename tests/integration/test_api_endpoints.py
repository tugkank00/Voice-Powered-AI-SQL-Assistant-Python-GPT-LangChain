import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
import json
import io
import urllib.parse

from app.main import app

from app.services.implementations.sql_query_service import SqlQueryService
from app.services.implementations.openai_text_to_sql import OpenAITextToSql
from app.services.implementations.langchain_executor import LangChainExecutor
from app.services.implementations.pdf_report_service import PDFReportService
from app.models.query_result import QueryResult
from app.exceptions.domain import (
    EmptyQuestionException,
    UnsafeSqlException,
    DatabaseExecutionException,
    InvalidRequestDataException,
    SqlGenerationException, 
    OpenAIServiceException
)

@pytest_asyncio.fixture(scope="module")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_ask_success(client: AsyncClient):
    question = "Show all users"
    generated_sql = "SELECT user_name FROM ai_service_usage;"
    db_result = [
        {"user_name": "user1"},
        {"user_name": "user2"}
    ]

    with patch.object(OpenAITextToSql, 'generate_sql', return_value=generated_sql) as mock_generate_sql, \
         patch.object(LangChainExecutor, 'execute', return_value=db_result) as mock_execute:
        
        response = await client.post("/ask", data={"question": question})

        assert response.status_code == 200
        assert question in response.text
        assert generated_sql in response.text
        assert "user1" in response.text
        assert "user2" in response.text
        assert "user_name" in response.text

        mock_generate_sql.assert_called_once_with(question)
        mock_execute.assert_called_once_with(generated_sql)

@pytest.mark.asyncio
async def test_ask_empty_question(client: AsyncClient):
    response = await client.post("/ask", data={"question": ""})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMPTY_QUESTION"
    assert "Question cannot be empty" in response.json()["error"]["message"]

@pytest.mark.asyncio
async def test_ask_unsafe_sql(client: AsyncClient):
    question = "Delete all data!"
    generated_sql = "DROP TABLE users;"

    with patch.object(OpenAITextToSql, 'generate_sql', return_value=generated_sql) as mock_generate_sql, \
         patch.object(LangChainExecutor, 'execute', side_effect=UnsafeSqlException(sql_query=generated_sql)) as mock_execute:
        
        response = await client.post("/ask", data={"question": question})

        assert response.status_code == 403 
        assert response.json()["error"]["code"] == "UNSAFE_SQL_DETECTED"
        assert "Only SELECT queries are allowed for security reasons" in response.json()["error"]["message"]
        mock_generate_sql.assert_called_once_with(question)
        mock_execute.assert_called_once_with(generated_sql)

@pytest.mark.asyncio
async def test_ask_database_execution_error(client: AsyncClient):
    question = "Show nonexistent column"
    generated_sql = "SELECT non_existent_column FROM ai_services;"

    with patch.object(OpenAITextToSql, 'generate_sql', return_value=generated_sql) as mock_generate_sql, \
         patch.object(LangChainExecutor, 'execute', side_effect=DatabaseExecutionException(sql_preview=generated_sql)) as mock_execute:
        
        response = await client.post("/ask", data={"question": question})

        assert response.status_code == 502  
        assert response.json()["error"]["code"] == "DATABASE_EXECUTION_ERROR"
        assert "Database query execution failed" in response.json()["error"]["message"]
        mock_generate_sql.assert_called_once_with(question)
        mock_execute.assert_called_once_with(generated_sql)

@pytest.mark.asyncio
async def test_download_report_pdf_success(client: AsyncClient):
    rows_data = [{"id": 1, "name": "Service A"}, {"id": 2, "name": "Service B"}]
    headers_data = ["id", "name"]
    question = "Service report"
    sql = "SELECT id, name FROM ai_services;"
    
    mock_pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</ProcSet[/PDF/Text]/Font<</F1 5 0 R>>>>endobj\n4 0 obj<</Length 44>>stream\nBT /F1 24 Tf 100 700 Td (Test PDF Content) Tj ET\nendstream\n5 0 obj<</Type/Font/Subtype/Type1/Name/F1/BaseFont/Helvetica>>endobj\nxref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000074 00000 n\n0000000150 00000 n\n0000000300 00000 n\n0000000393 00000 n\ntrailer<</Size 6/Root 1 0 R>>startxref\n492\n%%EOF"

    with patch.object(PDFReportService, 'generate_pdf', return_value=mock_pdf_bytes) as mock_generate_pdf:
        response = await client.post(
            "/download-report-pdf",
            data={
                "rows_json": json.dumps(rows_data),
                "headers_json": json.dumps(headers_data),
                "question": question,
                "sql": sql
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        safe_filename = urllib.parse.quote(question[:30].replace(" ", "_"))
        assert response.headers["content-disposition"] == f'attachment; filename="report_{safe_filename}.pdf"'
        assert response.content == mock_pdf_bytes
        
        mock_generate_pdf.assert_called_once()
        qr_arg = mock_generate_pdf.call_args[0][0]
        assert isinstance(qr_arg, QueryResult)
        assert qr_arg.question == question
        assert qr_arg.sql == sql
        assert qr_arg.headers == headers_data
        expected_qr_rows = [tuple(row.get(h, '') for h in headers_data) for row in rows_data]
        assert qr_arg.rows == expected_qr_rows

@pytest.mark.asyncio
async def test_download_report_pdf_empty_rows_json(client: AsyncClient):
    question = "Report"
    sql = "SELECT 1;"
    
    response = await client.post(
        "/download-report-pdf",
        data={
            "rows_json": "",
            "headers_json": json.dumps(["id"]),
            "question": question,
            "sql": sql
        }
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST_DATA"
    assert "No data provided for PDF generation" in response.json()["error"]["message"]

@pytest.mark.asyncio
async def test_download_report_pdf_invalid_rows_json(client: AsyncClient):
    question = "Report"
    sql = "SELECT 1;"
    
    response = await client.post(
        "/download-report-pdf",
        data={
            "rows_json": "not a json",
            "headers_json": json.dumps(["id"]),
            "question": question,
            "sql": sql
        }
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST_DATA"
    assert "Invalid JSON in rows_json" in response.json()["error"]["message"]

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "timestamp" in response.json()
    assert "version" in response.json()


@pytest.mark.asyncio
async def test_ask_sql_generation_failed(client: AsyncClient):
    question = "Invalid query"
    
    with patch.object(OpenAITextToSql, 'generate_sql', side_effect=SqlGenerationException(question=question)) as mock_generate_sql:
        response = await client.post("/ask", data={"question": question})

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "SQL_GENERATION_FAILED"
        assert "Failed to generate SQL query" in response.json()["error"]["message"]
        mock_generate_sql.assert_called_once_with(question)

@pytest.mark.asyncio
async def test_ask_openai_service_error(client: AsyncClient):
    question = "Show all users"
    
    with patch.object(OpenAITextToSql, 'generate_sql', side_effect=OpenAIServiceException(api_error="Service down")) as mock_generate_sql:
        response = await client.post("/ask", data={"question": question})

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "OPENAI_SERVICE_ERROR"
        assert "OpenAI service is temporarily unavailable" in response.json()["error"]["message"]
        mock_generate_sql.assert_called_once_with(question)    