from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


class DecisionSimulatorException(Exception):
    """Base exception for the application"""
    def __init__(self, message: str, status_code: int = 500, detail: str = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class LLMProcessingError(DecisionSimulatorException):
    """Error during LLM processing"""
    def __init__(self, message: str = "Error processing with LLM", detail: str = None):
        super().__init__(message, status_code=500, detail=detail)


class SimulationError(DecisionSimulatorException):
    """Error during simulation execution"""
    def __init__(self, message: str = "Simulation failed", detail: str = None):
        super().__init__(message, status_code=500, detail=detail)


class ExternalAPIError(DecisionSimulatorException):
    """Error calling external APIs"""
    def __init__(self, message: str = "External API error", detail: str = None):
        super().__init__(message, status_code=503, detail=detail)


class DataNotFoundError(DecisionSimulatorException):
    """Requested data not found"""
    def __init__(self, message: str = "Data not found", detail: str = None):
        super().__init__(message, status_code=404, detail=detail)


class AuthenticationError(DecisionSimulatorException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed", detail: str = None):
        super().__init__(message, status_code=401, detail=detail)


async def custom_exception_handler(request: Request, exc: DecisionSimulatorException):
    logger.error(f"Error: {exc.message}, Detail: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "detail": exc.detail
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": str(exc.detail),
            "detail": None
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    error_messages = [f"{err['loc'][-1]}: {err['msg']}" for err in errors]
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation error",
            "detail": "; ".join(error_messages)
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if __debug__ else None
        }
    )
