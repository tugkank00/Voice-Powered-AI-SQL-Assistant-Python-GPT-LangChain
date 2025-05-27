from typing import Optional, Dict, Any
from enum import Enum
import uuid
from datetime import datetime, timezone


class ErrorCode(Enum):
    # 400
    EMPTY_QUESTION = "EMPTY_QUESTION"
    INVALID_FILE_FORMAT = "INVALID_FILE_FORMAT"
    INVALID_REQUEST_DATA = "INVALID_REQUEST_DATA"
    
    # 403
    UNSAFE_SQL_DETECTED = "UNSAFE_SQL_DETECTED"
    UNAUTHORIZED_OPERATION = "UNAUTHORIZED_OPERATION"
    
    # 422
    SQL_GENERATION_FAILED = "SQL_GENERATION_FAILED"
    VOICE_TRANSCRIPTION_FAILED = "VOICE_TRANSCRIPTION_FAILED"
    REPORT_GENERATION_FAILED = "REPORT_GENERATION_FAILED"
    
    # 502/503
    OPENAI_SERVICE_ERROR = "OPENAI_SERVICE_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_EXECUTION_ERROR = "DATABASE_EXECUTION_ERROR"
    
    # 500
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


class BaseAppException(Exception):
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        http_status: int,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
        correlation_id: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.http_status = http_status
        self.details = details or {}
        self.original_exception = original_exception
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "correlation_id": self.correlation_id,
                "timestamp": self.timestamp,
                **self.details
            }
        }
    
    def __str__(self) -> str:
        return (f"{self.__class__.__name__}(code={self.error_code.value}, "
                f"message='{self.message}', correlation_id={self.correlation_id})")


class ValidationException(BaseAppException):
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        field: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop('details', {})
        if field:
            details['field'] = field
        
        super().__init__(
            message=message,
            error_code=error_code,
            http_status=400,
            details=details,
            **kwargs
        )


class SecurityException(BaseAppException):
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop('details', {})
        if operation:
            details['blocked_operation'] = operation
        
        super().__init__(
            message=message,
            error_code=error_code,
            http_status=403,
            details=details,
            **kwargs
        )


class ProcessingException(BaseAppException):
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        processing_stage: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop('details', {})
        if processing_stage:
            details['stage'] = processing_stage
        
        super().__init__(
            message=message,
            error_code=error_code,
            http_status=422,
            details=details,
            **kwargs
        )


class ExternalServiceException(BaseAppException):    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        service_name: Optional[str] = None,
        is_temporary: bool = True,
        **kwargs
    ):
        details = kwargs.pop('details', {})
        if service_name:
            details['service'] = service_name
        details['is_temporary'] = is_temporary
        
        http_status = 503 if is_temporary else 502
        
        super().__init__(
            message=message,
            error_code=error_code,
            http_status=http_status,
            details=details,
            **kwargs
        )


class InternalServerException(BaseAppException):    
    def __init__(
        self,
        message: str = "An internal server error occurred",
        error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        **kwargs
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            http_status=500,
            **kwargs
        )