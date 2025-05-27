import logging
import time
from app.models.query_result import QueryResult
from app.services.base.protocols import TextToSqlProtocol, SqlExecutorProtocol, QueryProcessorProtocol

from app.exceptions.domain import (
    EmptyQuestionException,
    UnsafeSqlException, 
    DatabaseExecutionException
)

class SqlQueryService(QueryProcessorProtocol):
    def __init__(self, text_to_sql_service: TextToSqlProtocol, sql_executor_service: SqlExecutorProtocol):
        self.logger = logging.getLogger(__name__)
        self.text_to_sql_service = text_to_sql_service
        self.sql_executor_service = sql_executor_service
    
    def process_question(self, question: str) -> QueryResult:
        if not question or question.strip() == "":
            raise EmptyQuestionException()
        
        start_time = time.time()
        sql = None
        
        try:
            sql = self.text_to_sql_service.generate_sql(question)
            self.logger.info(f"Generated SQL: {sql}") 
            
            result = self.sql_executor_service.execute(sql)
            
        except (UnsafeSqlException, DatabaseExecutionException) as e:
            execution_time = int((time.time() - start_time) * 1000)
            e.details['execution_time_ms'] = execution_time
            e.details['sql_query'] = sql
            raise e
        
        execution_time = int((time.time() - start_time) * 1000)
        self.logger.info(f"Query processed in {execution_time} ms")
        
        if not result:
            return QueryResult(
                question=question,
                headers=[],
                rows=[],
                execution_time_ms=execution_time,
                sql=sql,
                error="No results found for this query"
            )
        
        headers = list(result[0].keys())
        rows = [list(row.values()) for row in result]
        
        return QueryResult(
            question=question,
            headers=headers,
            rows=rows,
            execution_time_ms=execution_time,
            sql=sql
        )
