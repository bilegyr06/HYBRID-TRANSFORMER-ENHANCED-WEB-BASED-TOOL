"""
Centralized error handling for safe client responses and detailed server logging.

Security principle: Never expose system details to clients.
- Client: Generic safe messages ("An error occurred" / specific validation errors)
- Server: Full error details, stack traces, and context logged server-side

Usage:
    try:
        # operation
    except SpecificError as e:
        handle_error(e, "Failed to do thing")  # Returns generic HTTPException
Simplified error handling for the Literature Review Assistant.
"""

import logging
from typing import Optional, Type
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class ClientError(Exception):
    """Exception with safe message for clients (e.g., validation errors)."""
    def __init__(self, client_message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.client_message = client_message
        self.status_code = status_code
        super().__init__(client_message)


def handle_error(
    exception: Exception,
    operation: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    client_message: Optional[str] = None,
    log_level: str = "error",
) -> HTTPException:
    """
    Handle an exception safely by logging full details and returning generic message.
    
    Args:
        exception: The exception that occurred
        operation: What operation was being attempted (e.g., "upload file", "process documents")
        status_code: HTTP status code to return (default: 500)
        client_message: Custom safe message for client (auto-generated if None)
        log_level: Logging level ('error', 'warning', 'info')
    
    Returns:
        HTTPException with safe message for client
    
    Example:
        try:
            db.commit()
        except SQLAlchemyError as e:
            raise handle_error(e, "save user to database", status_code=status.HTTP_400_BAD_REQUEST)
    """
    
    # Log full error details server-side with context
    log_func = getattr(logger, log_level, logger.error)
    log_func(
        f"Error during {operation}: {type(exception).__name__}: {str(exception)}",
        f"Operation '{operation}' failed: {type(exception).__name__}",
        exc_info=True,
        extra={
            "operation": operation,
            "error_type": type(exception).__name__,
            "status_code": status_code,
        }
    )
    
    # Generate client message if not provided
    if client_message is None:
        client_message = _get_safe_client_message(exception, status_code)
        if isinstance(exception, (SQLAlchemyError, ValidationError)):
            client_message = "A data validation or database error occurred."
        else:
            client_message = "An internal error occurred. Please try again."
    
    return HTTPException(status_code=status_code, detail=client_message)


def handle_database_error(
    exception: SQLAlchemyError,
    operation: str,
    client_message: str = "Database operation failed. Please try again.",
) -> HTTPException:
    """
    Handle database-specific errors safely.
    
    Args:
        exception: SQLAlchemy exception
        operation: What operation was being attempted
        client_message: Safe message for client
    
    Returns:
        HTTPException with 400 for constraint/integrity errors, 500 for others
    """
    if isinstance(exception, IntegrityError):
        status_code = status.HTTP_400_BAD_REQUEST
        logger.warning(
            f"Database integrity error during {operation}: {str(exception.orig)}",
            exc_info=True,
        )
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        logger.error(
            f"Database error during {operation}: {str(exception)}",
            exc_info=True,
        )
    
    return HTTPException(status_code=status_code, detail=client_message)


def handle_validation_error(
    exception: ValidationError,
    operation: str,
) -> HTTPException:
    """
    Handle Pydantic validation errors with friendly message.
    
    Args:
        exception: Pydantic ValidationError
        operation: What operation was being validated
    
    Returns:
        HTTPException with 422 and field-level error details
    """
    # Extract field names from validation errors
    errors = exception.errors()
    field_errors = []
    
    for error in errors:
        field = ".".join(str(x) for x in error["loc"][1:])  # Skip "body" prefix
        msg = error["msg"]
        field_errors.append(f"{field}: {msg}")
    
    error_detail = "; ".join(field_errors) if field_errors else "Invalid input"
    
    logger.warning(
        f"Validation error during {operation}: {error_detail}",
        exc_info=False,  # Don't include stack trace for validation errors
    )
    
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=error_detail
    )


def _get_safe_client_message(exception: Exception, status_code: int) -> str:
    """Generate appropriate safe message based on exception type and status code."""
    
    if isinstance(exception, ClientError):
        return exception.client_message
    
    if isinstance(exception, ValidationError):
        return "Invalid input data. Please check your request and try again."
    
    if isinstance(exception, SQLAlchemyError):
        if isinstance(exception, IntegrityError):
            return "Resource already exists or violates business rules."
        return "Database operation failed. Please try again."
    
    if isinstance(exception, FileNotFoundError):
        return "File not found."
    
    if isinstance(exception, PermissionError):
        return "You don't have permission to access this resource."
    
    if isinstance(exception, TimeoutError):
        return "Operation timed out. Please try again."
    
    if status_code == status.HTTP_400_BAD_REQUEST:
        return "Invalid request. Please check your input and try again."
    
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return "Authentication required. Please log in."
    
    if status_code == status.HTTP_403_FORBIDDEN:
        return "You don't have permission to access this resource."
    
    if status_code == status.HTTP_404_NOT_FOUND:
        return "Resource not found."
    
    # Default: generic server error
    return "An error occurred. Please try again later."


def safe_operation(
    func,
    operation: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    expected_exception: Type[Exception] = Exception,
):
    """
    Decorator to wrap function calls with safe error handling.
    
    Args:
        func: Function to wrap
        operation: Description of operation (e.g., "extract PDF text")
        status_code: HTTP status code on error
        expected_exception: Exception type to catch (default: all)
    
    Usage:
        try:
            result = safe_operation(
                lambda: pdf.extract_text(),
                "extract text from PDF",
                expected_exception=PDFException
            )
        except HTTPException as e:
            raise e  # Already logged and safe
    """
    try:
        return func()
    except expected_exception as e:
        raise handle_error(e, operation, status_code)
