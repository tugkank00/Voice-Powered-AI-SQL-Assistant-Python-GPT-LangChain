import pytest
from unittest.mock import patch, MagicMock
import os
import openai 

from app.services.implementations.openai_text_to_sql import OpenAITextToSql
from app.exceptions.domain import SqlGenerationException, OpenAIServiceException, ConfigurationException

@pytest.fixture
def openai_text_to_sql_instance():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        yield OpenAITextToSql()

def test_generate_sql_success(openai_text_to_sql_instance):
    question = "Show all clients from USA"
    expected_sql = "SELECT * FROM ai_projects WHERE country = 'USA';"

    with patch("openai.chat.completions.create") as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = expected_sql
        mock_create.return_value = mock_response

        generated_sql = openai_text_to_sql_instance.generate_sql(question)
        assert generated_sql == expected_sql
        mock_create.assert_called_once()
        args, kwargs = mock_create.call_args
        assert kwargs["model"] == "gpt-4o"
        assert question in kwargs["messages"][0]["content"]

def test_generate_sql_empty_content(openai_text_to_sql_instance):
    question = "Some question"

    with patch("openai.chat.completions.create") as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "   "
        mock_create.return_value = mock_response

        with pytest.raises(SqlGenerationException):
            openai_text_to_sql_instance.generate_sql(question)

def test_generate_sql_openai_api_error(openai_text_to_sql_instance):
    question = "One more question"

    with patch("openai.chat.completions.create") as mock_create:
        mock_create.side_effect = openai.APIError("API error occurred", request=MagicMock(), body=MagicMock()) 

        with pytest.raises(OpenAIServiceException):
            openai_text_to_sql_instance.generate_sql(question)

def test_init_missing_api_key():
    original_api_key = os.environ.pop("OPENAI_API_KEY", None)
    
    with pytest.raises(ConfigurationException) as excinfo:
        OpenAITextToSql()
    assert "OPENAI_API_KEY" in str(excinfo.value)
    
    if original_api_key is not None:
        os.environ["OPENAI_API_KEY"] = original_api_key

def test_generate_sql_strips_markdown(openai_text_to_sql_instance):
    question = "Use report"
    raw_sql_with_markdown = "```sql\nSELECT * FROM usage;\n```"
    expected_sql = "SELECT * FROM usage;"

    with patch("openai.chat.completions.create") as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = raw_sql_with_markdown
        mock_create.return_value = mock_response

        generated_sql = openai_text_to_sql_instance.generate_sql(question)
        assert generated_sql == expected_sql