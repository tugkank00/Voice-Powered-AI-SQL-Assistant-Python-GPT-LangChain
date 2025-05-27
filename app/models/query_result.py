from typing import List, Tuple, Optional

class QueryResult:
    def __init__(
        self,
        question: str,
        headers: List[str],
        rows: List[Tuple],
        execution_time_ms: int,
        sql: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.question = question
        self.headers = headers
        self.rows = rows
        self.execution_time_ms = execution_time_ms
        self.sql = sql
        self.error = error

    def has_results(self) -> bool:
        return bool(self.headers and self.rows and not self.error)
