from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class ErrorDetail(BaseModel):
    code: str = Field(..., description="Unique error code")
    message: str = Field(..., description="Description of the error")
    correlation_id: str = Field(..., description="ID for tracing errors")
    timestamp: str = Field(..., description="Error time in ISO format")
    field: Optional[str] = Field(None, description="A field that caused a mistake (for Validation Errors)")
    service: Optional[str] = Field(None, description="External service that caused an error")
    stage: Optional[str] = Field(None, description="The processing stage at which an error occurred")

class ErrorResponse(BaseModel):
    error: ErrorDetail

class ValidationErrorResponse(ErrorResponse):
    pass

class SecurityErrorResponse(ErrorResponse):
    pass

class ProcessingErrorResponse(ErrorResponse):
    pass

class ServiceUnavailableResponse(ErrorResponse):
    pass

class InternalErrorResponse(ErrorResponse):
    pass

COMMON_RESPONSES = {
    400: {
        "description": "Validation Error - Invalid input data",
        "model": ValidationErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "empty_question": {
                        "summary": "Empty question",
                        "value": {
                            "error": {
                                "code": "EMPTY_QUESTION",
                                "message": "Question cannot be empty",
                                "correlation_id": "abc-123-def",
                                "timestamp": "2025-01-15T10:30:00Z",
                                "field": "question"
                            }
                        }
                    },
                    "invalid_file": {
                        "summary": "Invalid file format",
                        "value": {
                            "error": {
                                "code": "INVALID_FILE_FORMAT", 
                                "message": "Invalid file format: txt",
                                "correlation_id": "xyz-456-abc",
                                "timestamp": "2025-01-15T10:30:00Z",
                                "field": "file",
                                "supported_formats": ["mp3", "wav", "ogg"]
                            }
                        }
                    }
                }
            }
        }
    },
    403: {
        "description": "Security Error - Operation not allowed",
        "model": SecurityErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "unsafe_sql": {
                        "summary": "Unsafe SQL detected",
                        "value": {
                            "error": {
                                "code": "UNSAFE_SQL_DETECTED",
                                "message": "Only SELECT queries are allowed for security reasons",
                                "correlation_id": "sec-789-def",
                                "timestamp": "2025-01-15T10:30:00Z",
                                "blocked_operation": "sql_execution",
                                "sql_preview": "DELETE FROM users WHERE..."
                            }
                        }
                    }
                }
            }
        }
    },
    422: {
        "description": "Processing Error - Cannot process the request",
        "model": ProcessingErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "sql_generation_failed": {
                        "summary": "SQL generation failed",
                        "value": {
                            "error": {
                                "code": "SQL_GENERATION_FAILED",
                                "message": "Failed to generate SQL query from the question",
                                "correlation_id": "proc-123-abc",
                                "timestamp": "2025-01-15T10:30:00Z",
                                "stage": "sql_generation",
                                "question_preview": "What is the meaning of life and..."
                            }
                        }
                    },
                    "voice_transcription_failed": {
                        "summary": "Voice transcription failed",
                        "value": {
                            "error": {
                                "code": "VOICE_TRANSCRIPTION_FAILED",
                                "message": "Failed to transcribe voice input",
                                "correlation_id": "voice-456-def",
                                "timestamp": "2025-01-15T10:30:00Z",
                                "stage": "voice_transcription",
                                "file_size": 1024000,
                                "file_path": "/tmp/audio.mp3"
                            }
                        }
                    }
                }
            }
        }
    },
    502: {
        "description": "Bad Gateway - External service error",
        "model": ServiceUnavailableResponse,
        "content": {
            "application/json": {
                "examples": {
                    "openai_error": {
                        "summary": "OpenAI service error",
                        "value": {
                            "error": {
                                "code": "OPENAI_SERVICE_ERROR",
                                "message": "OpenAI service is temporarily unavailable",
                                "correlation_id": "ext-789-ghi",
                                "timestamp": "2025-01-15T10:30:00Z",
                                "service": "OpenAI",
                                "is_temporary": True,
                                "api_error": "Rate limit exceeded"
                            }
                        }
                    }
                }
            }
        }
    },
    503: {
        "description": "Service Unavailable - Database or external service temporarily down",
        "model": ServiceUnavailableResponse,
        "content": {
            "application/json": {
                "examples": {
                    "database_unavailable": {
                        "summary": "Database connection failed",
                        "value": {
                            "error": {
                                "code": "DATABASE_CONNECTION_ERROR",
                                "message": "Database connection failed", 
                                "correlation_id": "db-123-jkl",
                                "timestamp": "2025-01-15T10:30:00Z",
                                "service": "PostgreSQL",
                                "is_temporary": True
                            }
                        }
                    }
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error - Unexpected error occurred",
        "model": InternalErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "internal_error": {
                        "summary": "Unexpected server error",
                        "value": {
                            "error": {
                                "code": "INTERNAL_SERVER_ERROR",
                                "message": "An unexpected error occurred. Please try again later.",
                                "correlation_id": "int-456-mno",
                                "timestamp": "2025-01-15T10:30:00Z"
                            }
                        }
                    }
                }
            }
        }
    }
}

def add_common_responses(additional_responses: Dict = None):
    def decorator(func):
        responses = COMMON_RESPONSES.copy()
        if additional_responses:
            responses.update(additional_responses)
        
        if not hasattr(func, '__annotations__'):
            func.__annotations__ = {}
        
        func.__responses__ = responses
        return func
    
    return decorator