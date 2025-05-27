from typing import Protocol, List, Tuple, Optional, Dict, Any

from app.models.query_result import QueryResult

class TextToSqlProtocol(Protocol):
    """Convert a natural language question into a SQL query."""
    def generate_sql(self, question: str) -> str:
        ...

class SqlExecutorProtocol(Protocol):
    """Execute a SQL query and return the results as a list of headers and rows."""
    def execute(self, sql: str) -> List[Tuple]: 
        ...

class VoiceToTextProtocol(Protocol):
    """Transcribe voice to text."""
    def transcribe(self, filepath: str) -> str:
        ...

class ReportGeneratorProtocol(Protocol):
    """Generate a PDF report based on the query result, returning raw bytes of the PDF file."""
    def generate_pdf(self, query_result: QueryResult) -> bytes:
        ...

class QueryProcessorProtocol(Protocol):
    """Process a natural language question and return the query result."""
    def process_question(self, question: str) -> QueryResult:
        ...
