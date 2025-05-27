from ast import Tuple
import logging
from langchain_community.utilities.sql_database import SQLDatabase
from typing import Protocol, List, Dict, Any
from dotenv import load_dotenv
import os
from sqlalchemy import text

from app.exceptions.domain import (
    UnsafeSqlException,
    DatabaseExecutionException,
    DatabaseConnectionException,
    ConfigurationException
)
from app.services.base.protocols import SqlExecutorProtocol
load_dotenv()

class LangChainExecutor(SqlExecutorProtocol):
    def __init__(self, db_url: str = None):
        self.logger = logging.getLogger(__name__)
        
        db_url = db_url or os.getenv("DATABASE_URL")
        if not db_url:
            raise ConfigurationException("DATABASE_URL")
        
        try:
            self.db = SQLDatabase.from_uri(db_url, include_tables=["ai_services", "ai_projects", "ai_service_usage"])
            self.engine = self.db._engine
        except Exception as e:
            raise DatabaseConnectionException(
                original_exception=e,
                details={"db_url_provided": bool(db_url)}
            )
    
    def execute(self, sql: str) -> List[Tuple]:
        self.logger.info(f"Executing SQL query: {sql}")
        
        if not self._is_safe_query(sql):
            self.logger.warning(f"Unsafe SQL blocked: {sql}")
            raise UnsafeSqlException(sql_query=sql)
        
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(sql))
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                
                self.logger.debug(f"Query returned {len(rows)} rows")
                return rows
                
        except Exception as e:
            self.logger.exception("Database execution error")
            raise DatabaseExecutionException(
                sql_preview=sql[:100] + "..." if len(sql) > 100 else sql,
                original_exception=e,
                details={
                    "error_type": type(e).__name__,
                    "query_length": len(sql)
                }
            )
    
    def _is_safe_query(self, sql: str) -> bool:
        normalized_sql = sql.strip().upper()
        return (normalized_sql.startswith("SELECT") and
                all(keyword not in normalized_sql for keyword in
                    ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", "EXEC", "EXECUTE"]))


