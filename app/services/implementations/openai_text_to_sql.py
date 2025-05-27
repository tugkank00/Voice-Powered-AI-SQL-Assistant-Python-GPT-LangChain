import logging
import openai
import os
from typing import Protocol

from app.exceptions.domain import (
    SqlGenerationException,
    OpenAIServiceException,
    ConfigurationException
)
from app.services.base.protocols import TextToSqlProtocol

class OpenAITextToSql(TextToSqlProtocol):
    DATABASE_SCHEMA = """
Table ai_services (
    id: int,
    name: string,
    provider: string,
    model: string,
    type: string,
    input_price_per_1k_tokens: decimal,
    output_price_per_1k_tokens: decimal,
    supports_sql: boolean,
    max_tokens: int,
    context_window: string,
    available: boolean,
    launched_at: date,
    description: text
)

Table ai_projects (
    id: int,
    client_name: string,
    industry: string,
    country: string
)

Table ai_service_usage (
    id: int,
    service_id: int (FK to ai_services.id),
    client_id: int (FK to ai_projects.id),
    user_name: string,
    usage_date: date,
    prompt_tokens: int,
    completion_tokens: int
)
"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ConfigurationException("OPENAI_API_KEY")
        
        openai.api_key = api_key
        
    def generate_sql(self, question: str) -> str:
        self.logger.info(f"Generating SQL for question: {question}")
        
        prompt = f"""
You are an SQL expert. Convert the question to an SQL query using the tables provided below.

SCHEMA:
{self.DATABASE_SCHEMA}

INSTRUCTIONS:
- Use the correct tables based on context.
- For questions containing 'full', 'all', or implying complete data from ai_service_usage or ai_projects (e.g., usage reports, user activity, token usage, client-related queries like countries or projects), use LEFT JOIN to include all records from the primary table (ai_service_usage or ai_projects), even if service_id or client_id is NULL.
- For fields from joined tables that may be NULL (e.g., s.model, s.name, p.client_name, p.country), use COALESCE to return 'Unknown' instead of NULL.
- For other questions, use INNER JOIN unless specified otherwise.
- Return ONLY the SQL query (no explanation, no comments, no Markdown).
- Date format is YYYY-MM-DD.
- Ensure the query is compatible with PostgreSQL.

EXAMPLES:
Question: Full usage report for all services and users
SQL: SELECT u.prompt_tokens, u.completion_tokens, u.usage_date, COALESCE(s.name, 'Unknown') AS service_name, u.user_name, COALESCE(p.client_name, 'Unknown') AS client_name, COALESCE(p.country, 'Unknown') AS country
FROM ai_service_usage u
LEFT JOIN ai_services s ON u.service_id = s.id
LEFT JOIN ai_projects p ON u.client_id = p.id;

Question: All active user by total token usage
SQL: SELECT u.user_name, SUM(u.prompt_tokens + u.completion_tokens) AS total_tokens
FROM ai_service_usage u
LEFT JOIN ai_services s ON u.service_id = s.id
WHERE s.available = TRUE OR s.available IS NULL
GROUP BY u.user_name;

Question: How many times each model was used?
SQL: SELECT COALESCE(s.model, 'Unknown') AS model, COUNT(u.id) AS usage_count
FROM ai_service_usage u
LEFT JOIN ai_services s ON u.service_id = s.id
GROUP BY s.model;

Question: All countries where clients have used any service
SQL: SELECT DISTINCT COALESCE(p.country, 'Unknown') AS country
FROM ai_projects p
LEFT JOIN ai_service_usage u ON p.id = u.client_id;

Question: Show usages where no project is associated
SQL: SELECT u.* FROM ai_service_usage u WHERE u.client_id IS NULL;

QUESTION: {question}
SQL:
"""
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=150
            )
       
            content = response.choices[0].message.content
            if not content or content.isspace():
                raise SqlGenerationException(
                    question=question,
                    details={"reason": "OpenAI returned empty content"}
                )
                
            if content.startswith("```sql"):
                content = content.replace("```sql", "").replace("```", "").strip()
            
            content = content.strip()
            self.logger.debug(f"Generated SQL: {content}")
            return content
            
        except openai.APIError as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise OpenAIServiceException(
                api_error=str(e),
                original_exception=e,
                details={
                    "question_length": len(question),
                    "api_error_type": type(e).__name__
                }
            )
        except Exception as e:
            self.logger.error(f"SQL generation error: {e}")
            raise SqlGenerationException(
                question=question,
                original_exception=e,
                details={
                    "error_type": type(e).__name__,
                    "question_length": len(question)
                }
            )
