import pytest
from unittest.mock import patch, MagicMock
import os
from sqlalchemy import text
from typing import List, Dict, Any, Tuple 

from app.services.implementations.langchain_executor import LangChainExecutor

from app.exceptions.domain import (
    UnsafeSqlException,
    DatabaseExecutionException,
    DatabaseConnectionException,
    ConfigurationException
)

@pytest.fixture
def langchain_executor_instance():
    with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"}):
        with patch("langchain_community.utilities.sql_database.SQLDatabase.from_uri") as mock_from_uri:
            mock_db = MagicMock()
            mock_engine = MagicMock()
            mock_db._engine = mock_engine
            mock_from_uri.return_value = mock_db
            yield LangChainExecutor()

@pytest.fixture
def langchain_executor_missing_db_url():
    original_db_url = os.environ.pop("DATABASE_URL", None)
    yield
    if original_db_url is not None:
        os.environ["DATABASE_URL"] = original_db_url

def test_init_missing_db_url(langchain_executor_missing_db_url):
    with pytest.raises(ConfigurationException) as excinfo:
        LangChainExecutor()
    assert "DATABASE_URL" in str(excinfo.value)

def test_init_db_connection_error():
    with patch.dict(os.environ, {"DATABASE_URL": "invalid_url"}):
        with patch("langchain_community.utilities.sql_database.SQLDatabase.from_uri") as mock_from_uri:
            mock_from_uri.side_effect = Exception("Connection failed")
            with pytest.raises(DatabaseConnectionException) as excinfo:
                LangChainExecutor() 
            assert "Database connection failed" in str(excinfo.value)

def test_execute_success(langchain_executor_instance):
    sql_query = "SELECT id, name FROM ai_services WHERE id = 1;"
    
    mock_result = MagicMock()
    mock_result.keys.return_value = ["id", "name"]
    mock_result.fetchall.return_value = [(1, "Service A"), (2, "Service B")] 

    mock_connection = MagicMock()
    mock_connection.execute.return_value = mock_result
    langchain_executor_instance.engine.connect.return_value.__enter__.return_value = mock_connection

    expected_rows = [{"id": 1, "name": "Service A"}, {"id": 2, "name": "Service B"}] 
    
    result = langchain_executor_instance.execute(sql_query)
    assert result == expected_rows
    
    mock_connection.execute.assert_called_once()
    assert mock_connection.execute.call_args[0][0].text == sql_query

def test_execute_unsafe_sql(langchain_executor_instance):
    unsafe_sql = "DROP TABLE ai_services;"
    with pytest.raises(UnsafeSqlException) as excinfo:
        langchain_executor_instance.execute(unsafe_sql)
    assert "Only SELECT queries are allowed for security reasons" in str(excinfo.value) 

def test_execute_db_execution_error(langchain_executor_instance):
    sql_query = "SELECT non_existent_column FROM ai_services;"
    
    mock_connection = MagicMock()
    mock_connection.execute.side_effect = Exception("SQL syntax error")
    langchain_executor_instance.engine.connect.return_value.__enter__.return_value = mock_connection

    with pytest.raises(DatabaseExecutionException) as excinfo:
        langchain_executor_instance.execute(sql_query)
    assert "Database query execution failed" in str(excinfo.value)

def test_is_safe_query():
    with patch("langchain_community.utilities.sql_database.SQLDatabase.from_uri"):
        executor = LangChainExecutor(db_url="sqlite:///:memory:")

    assert executor._is_safe_query("SELECT * FROM users;") is True
    assert executor._is_safe_query("select id from products;") is True
    assert executor._is_safe_query(" SELECT name FROM customers WHERE id = 1;") is True
    assert executor._is_safe_query("SELECT column FROM table WHERE keyword LIKE '%INSERT%';") is False 

    assert executor._is_safe_query("INSERT INTO users VALUES ('test');") is False
    assert executor._is_safe_query("UPDATE users SET name = 'new_name';") is False
    assert executor._is_safe_query("DELETE FROM users;") is False
    assert executor._is_safe_query("DROP TABLE users;") is False
    assert executor._is_safe_query("ALTER TABLE users ADD COLUMN age INT;") is False
    assert executor._is_safe_query("TRUNCATE TABLE users;") is False
    assert executor._is_safe_query("CREATE TABLE users (id INT);") is False
    assert executor._is_safe_query("EXEC some_proc;") is False
    assert executor._is_safe_query("EXECUTE some_other_proc;") is False
    assert executor._is_safe_query("SELECT * FROM users; DROP TABLE sensitive_data;") is False
    
    assert executor._is_safe_query("sELECt * FrOm TablE;") is True
    assert executor._is_safe_query("Insert INTO users VALUES (1);") is False