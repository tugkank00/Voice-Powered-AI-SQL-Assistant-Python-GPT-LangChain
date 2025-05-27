import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions.base import BaseAppException, ErrorCode, InternalServerException


class ExceptionHandler:
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._error_counters: Dict[str, int] = {}
    
    def increment_error_counter(self, error_code: str):
        self._error_counters[error_code] = self._error_counters.get(error_code, 0) + 1
    
    def get_error_stats(self) -> Dict[str, int]:
        return self._error_counters.copy()
    
    async def handle_app_exception(
        self, 
        request: Request, 
        exc: BaseAppException
    ) -> JSONResponse:
        log_data = {
            "correlation_id": exc.correlation_id,
            "error_code": exc.error_code.value,
            "path": str(request.url),
            "method": request.method,
            "user_agent": request.headers.get("user-agent", "unknown"),
            "details": exc.details
        }

        if exc.http_status >= 500:
            self.logger.error(
                f"Internal error: {exc.message}",
                extra=log_data,
                exc_info=exc.original_exception
            )
        elif exc.http_status >= 400:
            self.logger.warning(
                f"Client error: {exc.message}",
                extra=log_data
            )
        else:
            self.logger.info(
                f"Handled exception: {exc.message}",
                extra=log_data
            )

        self.increment_error_counter(exc.error_code.value)
        return JSONResponse(
            status_code=exc.http_status,
            content=exc.to_dict()
        )
    
    async def handle_validation_error(
        self, 
        request: Request, 
        exc: RequestValidationError
    ) -> JSONResponse:
        
        from app.exceptions.domain import InvalidRequestDataException
        validation_errors = []
        for error in exc.errors():
            field = ".".join(str(x) for x in error.get("loc", []))
            message = error.get("msg", "Validation error")
            validation_errors.append(f"{field}: {message}")
        
        app_exc = InvalidRequestDataException(
            field_name="request_body",
            reason="; ".join(validation_errors),
            details={"validation_errors": exc.errors()}
        )
        
        return await self.handle_app_exception(request, app_exc)
    
    async def handle_http_exception(
        self, 
        request: Request, 
        exc: HTTPException
    ) -> JSONResponse:
        
        if exc.status_code == 404:
            error_code = ErrorCode.INTERNAL_SERVER_ERROR  
        else:
            error_code = ErrorCode.INTERNAL_SERVER_ERROR
        
        app_exc = InternalServerException(
            message=exc.detail or "HTTP error occurred",
            error_code=error_code,
            details={"http_status": exc.status_code}
        )
        app_exc.http_status = exc.status_code  
        
        return await self.handle_app_exception(request, app_exc)
    
    async def handle_unexpected_exception(
        self, 
        request: Request, 
        exc: Exception
    ) -> JSONResponse:
        correlation_id = str(id(exc))  

        self.logger.critical(
            f"Unexpected exception: {type(exc).__name__}: {str(exc)}",
            extra={
                "correlation_id": correlation_id,
                "path": str(request.url),
                "method": request.method,
                "traceback": traceback.format_exc()
            },
            exc_info=True
        )

        app_exc = InternalServerException(
            message="An unexpected error occurred. Please try again later.",
            correlation_id=correlation_id,
            original_exception=exc
        )
        
        self.increment_error_counter("UNEXPECTED_ERROR")
        
        return JSONResponse(
            status_code=500,
            content=app_exc.to_dict()
        )

exception_handler = ExceptionHandler()

async def app_exception_handler(request: Request, exc: BaseAppException):
    return await exception_handler.handle_app_exception(request, exc)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return await exception_handler.handle_validation_error(request, exc)

async def http_exception_handler(request: Request, exc: HTTPException):
    return await exception_handler.handle_http_exception(request, exc)

async def unexpected_exception_handler(request: Request, exc: Exception):
    return await exception_handler.handle_unexpected_exception(request, exc)