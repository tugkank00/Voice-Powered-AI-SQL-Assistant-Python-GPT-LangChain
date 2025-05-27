from fastapi import Depends
from app.services.base.protocols import (
    TextToSqlProtocol,
    SqlExecutorProtocol,
    QueryProcessorProtocol,
    VoiceToTextProtocol,
    ReportGeneratorProtocol,
)
from app.services.implementations.openai_text_to_sql import OpenAITextToSql
from app.services.implementations.langchain_executor import LangChainExecutor
from app.services.implementations.sql_query_service import SqlQueryService
from app.services.implementations.openai_whisper_service import OpenAIWhisperService
from app.services.implementations.pdf_report_service import PDFReportService
import os
from dotenv import load_dotenv

load_dotenv()

def get_text_to_sql_service() -> TextToSqlProtocol:
    return OpenAITextToSql()

def get_sql_executor_service() -> SqlExecutorProtocol:
    return LangChainExecutor(db_url=os.getenv("DATABASE_URL"))

def get_sql_query_service(
    text_to_sql: TextToSqlProtocol = Depends(get_text_to_sql_service),
    sql_executor: SqlExecutorProtocol = Depends(get_sql_executor_service)
) -> QueryProcessorProtocol:
    return SqlQueryService(text_to_sql, sql_executor)

def get_voice_to_text_service() -> VoiceToTextProtocol:
    return OpenAIWhisperService()

def get_report_service() -> ReportGeneratorProtocol:
    return PDFReportService()