from typing import Optional, Dict, Any
from .base import(ValidationException, 
                   ProcessingException, 
                   SecurityException, 
                   ExternalServiceException, 
                   InternalServerException, 
                   ErrorCode)


class EmptyQuestionException(ValidationException):
    
    def __init__(self, **kwargs):
        super().__init__(
            message="Question cannot be empty",
            error_code=ErrorCode.EMPTY_QUESTION,
            field="question",
            **kwargs
        )


class InvalidFileFormatException(ValidationException):
    def __init__(self, file_type: Optional[str] = None, **kwargs):
        message = "Invalid file format"
        if file_type:
            message += f": {file_type}"
        
        details = kwargs.pop('details', {})
        if file_type:
            details['file_type'] = file_type
            details['supported_formats'] = ['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm']
        
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_FILE_FORMAT,
            field="file",
            details=details,
            **kwargs
        )

class InvalidRequestDataException(ValidationException):
    def __init__(self, field_name: str, reason: str, **kwargs):
        super().__init__(
            message=f"Invalid {field_name}: {reason}",
            error_code=ErrorCode.INVALID_REQUEST_DATA,
            field=field_name,
            **kwargs
        )

class UnsafeSqlException(SecurityException):
    def __init__(self, sql_query: Optional[str] = None, **kwargs):
        details = kwargs.pop('details', {})
        if sql_query:
            details['sql_preview'] = sql_query[:50] + "..." if len(sql_query) > 50 else sql_query
        
        super().__init__(
            message="Only SELECT queries are allowed for security reasons",
            error_code=ErrorCode.UNSAFE_SQL_DETECTED,
            operation="sql_execution",
            details=details,
            **kwargs
        )

class SqlGenerationException(ProcessingException):
    def __init__(self, question: Optional[str] = None, **kwargs):
        details = kwargs.pop('details', {})
        if question:
            details['question_preview'] = question[:100] + "..." if len(question) > 100 else question
        
        super().__init__(
            message="Failed to generate SQL query from the question",
            error_code=ErrorCode.SQL_GENERATION_FAILED,
            processing_stage="sql_generation",
            details=details,
            **kwargs
        )

class VoiceTranscriptionException(ProcessingException):
    def __init__(self, file_info: Optional[Dict[str, Any]] = None, **kwargs):
        details = kwargs.pop('details', {})
        if file_info:
            details.update(file_info)
        
        super().__init__(
            message="Failed to transcribe voice input",
            error_code=ErrorCode.VOICE_TRANSCRIPTION_FAILED,
            processing_stage="voice_transcription",
            details=details,
            **kwargs
        )

class ReportGenerationException(ProcessingException):    
    def __init__(self, report_type: str = "PDF", **kwargs):
        details = kwargs.pop('details', {})
        details['report_type'] = report_type
        
        super().__init__(
            message=f"Failed to generate {report_type} report",
            error_code=ErrorCode.REPORT_GENERATION_FAILED,
            processing_stage="report_generation",
            details=details,
            **kwargs
        )

class OpenAIServiceException(ExternalServiceException):
    def __init__(self, api_error: Optional[str] = None, **kwargs):
        details = kwargs.pop('details', {})
        if api_error:
            details['api_error'] = api_error
        
        super().__init__(
            message="OpenAI service is temporarily unavailable",
            error_code=ErrorCode.OPENAI_SERVICE_ERROR,
            service_name="OpenAI",
            is_temporary=True,
            details=details,
            **kwargs
        )

class DatabaseConnectionException(ExternalServiceException):
    def __init__(self, **kwargs):
        super().__init__(
            message="Database connection failed",
            error_code=ErrorCode.DATABASE_CONNECTION_ERROR,
            service_name="PostgreSQL",
            is_temporary=True,
            **kwargs
        )

class DatabaseExecutionException(ExternalServiceException):    
    def __init__(self, sql_preview: Optional[str] = None, **kwargs):
        details = kwargs.pop('details', {})
        if sql_preview:
            details['sql_preview'] = sql_preview
        
        super().__init__(
            message="Database query execution failed",
            error_code=ErrorCode.DATABASE_EXECUTION_ERROR,
            service_name="PostgreSQL",
            is_temporary=False,
            details=details,
            **kwargs
        )

class ConfigurationException(InternalServerException):
    def __init__(self, config_key: str, **kwargs):
        details = kwargs.pop('details', {})
        details['config_key'] = config_key
        
        super().__init__(
            message=f"Configuration error: {config_key} not found or invalid",
            error_code=ErrorCode.CONFIGURATION_ERROR,
            details=details,
            **kwargs
        )