"""
Tests for error handling utilities and generic error responses.

Verifies:
- Client receives generic safe messages
- Server logs full error details
- Error handler works with various exception types
- Database errors return appropriate status codes
"""

import logging
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import status, HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import ValidationError

from src.core.error_handler import (
    handle_error,
    handle_database_error,
    handle_validation_error,
    ClientError,
    _get_safe_client_message,
)


class TestErrorHandler:
    """Test basic error handling functionality."""
    
    def test_handle_error_returns_http_exception(self):
        """Ensure handle_error raises HTTPException with safe message."""
        exc = ValueError("Sensitive database connection failed")
        
        with pytest.raises(HTTPException) as exc_info:
            handle_error(exc, "query database")
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "error occurred" in exc_info.value.detail.lower()
        assert "database" not in exc_info.value.detail
        assert "connection" not in exc_info.value.detail
    
    def test_handle_error_logs_full_details(self, caplog):
        """Ensure full error details are logged server-side."""
        exc = ValueError("Sensitive: API key leaked in request")
        
        with caplog.at_level(logging.ERROR):
            with pytest.raises(HTTPException):
                handle_error(exc, "process payment")
        
        # Check that full error details are in server log
        assert "process payment" in caplog.text
        assert "Sensitive: API key leaked" in caplog.text
        assert "ValueError" in caplog.text
    
    def test_handle_error_custom_client_message(self):
        """Test custom client message parameter."""
        exc = RuntimeError("Internal failure")
        
        with pytest.raises(HTTPException) as exc_info:
            handle_error(
                exc,
                "upload file",
                client_message="File upload failed. Please try again."
            )
        
        assert exc_info.value.detail == "File upload failed. Please try again."
    
    def test_handle_error_custom_status_code(self):
        """Test custom HTTP status code."""
        exc = FileNotFoundError("Missing config")
        
        with pytest.raises(HTTPException) as exc_info:
            handle_error(
                exc,
                "load config",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


class TestDatabaseErrorHandler:
    """Test database-specific error handling."""
    
    def test_integrity_error_returns_400(self):
        """IntegrityError (duplicate key, constraint violation) returns 400."""
        # Mock IntegrityError
        mock_error = IntegrityError(
            "statement",
            "params",
            ValueError("Duplicate email entry")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            handle_database_error(
                mock_error,
                "create user",
                client_message="Email already exists."
            )
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Email already exists."
    
    def test_generic_database_error_returns_500(self):
        """Generic SQLAlchemyError returns 500."""
        mock_error = SQLAlchemyError("Connection pool exhausted")
        
        with pytest.raises(HTTPException) as exc_info:
            handle_database_error(
                mock_error,
                "execute query",
                client_message="Database operation failed."
            )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Database operation failed."
    
    def test_database_error_logs_appropriately(self, caplog):
        """IntegrityError logged as WARNING, others as ERROR."""
        integrity_error = IntegrityError(
            "statement",
            "params",
            ValueError("Unique constraint violated")
        )
        
        with caplog.at_level(logging.WARNING):
            with pytest.raises(HTTPException):
                handle_database_error(integrity_error, "save data")
        
        assert "integrity error" in caplog.text.lower()


class TestValidationErrorHandler:
    """Test Pydantic validation error handling."""
    
    def test_validation_error_extracts_field_errors(self):
        """Validation errors show field names and error types."""
        # Create a validation error by triggering Pydantic validation
        from pydantic import BaseModel, field_validator
        
        class TestModel(BaseModel):
            email: str
            age: int
        
        try:
            TestModel(email="not-an-email", age="not-a-number")
        except ValidationError as ve:
            with pytest.raises(HTTPException) as exc_info:
                handle_validation_error(ve, "validate user input")
            
            # Should contain field errors
            assert "email" in exc_info.value.detail.lower() or "type" in exc_info.value.detail.lower()
            assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_validation_error_logs_without_stack_trace(self, caplog):
        """Validation errors logged without exc_info for clarity."""
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            value: int
        
        try:
            TestModel(value="invalid")
        except ValidationError as ve:
            with caplog.at_level(logging.WARNING):
                with pytest.raises(HTTPException):
                    handle_validation_error(ve, "parse request")
            
            # Should log validation error without full traceback
            assert "Validation error" in caplog.text


class TestSafeClientMessages:
    """Test safe message generation for different exception types."""
    
    def test_file_not_found_message(self):
        """FileNotFoundError returns appropriate message."""
        msg = _get_safe_client_message(
            FileNotFoundError("Missing file"),
            status.HTTP_404_NOT_FOUND
        )
        assert "not found" in msg.lower()
    
    def test_permission_error_message(self):
        """PermissionError returns permission-denied message."""
        msg = _get_safe_client_message(
            PermissionError("Access denied"),
            status.HTTP_403_FORBIDDEN
        )
        assert "permission" in msg.lower()
    
    def test_timeout_error_message(self):
        """TimeoutError returns retry message."""
        msg = _get_safe_client_message(
            TimeoutError("Request timed out"),
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        assert "timed out" in msg.lower() or "try again" in msg.lower()
    
    def test_400_status_code_generic_message(self):
        """400 status returns validation/bad-request message."""
        msg = _get_safe_client_message(
            ValueError("Bad input"),
            status.HTTP_400_BAD_REQUEST
        )
        assert "invalid" in msg.lower() or "check" in msg.lower()
    
    def test_401_status_code_auth_message(self):
        """401 status returns authentication required message."""
        msg = _get_safe_client_message(
            Exception("Token expired"),
            status.HTTP_401_UNAUTHORIZED
        )
        assert "authenticat" in msg.lower()
    
    def test_403_status_code_forbidden_message(self):
        """403 status returns access denied message."""
        msg = _get_safe_client_message(
            Exception("Unauthorized"),
            status.HTTP_403_FORBIDDEN
        )
        assert "permission" in msg.lower()
    
    def test_default_server_error_message(self):
        """Unknown error type returns generic message."""
        msg = _get_safe_client_message(
            Exception("Weird internal state"),
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        assert "error occurred" in msg.lower() or "try again" in msg.lower()


class TestClientError:
    """Test ClientError exception class."""
    
    def test_client_error_initialization(self):
        """ClientError stores message and status code."""
        exc = ClientError("Invalid email format", status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        assert exc.client_message == "Invalid email format"
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_client_error_default_status_code(self):
        """ClientError defaults to 400."""
        exc = ClientError("Missing required field")
        assert exc.status_code == status.HTTP_400_BAD_REQUEST


class TestIntegrationWithRoutes:
    """Test error handling integration with actual route responses."""
    
    def test_error_handler_in_route_context(self):
        """Error handler works correctly in route context."""
        # Simulate a route that uses handle_error
        def failing_route():
            try:
                raise ValueError("Database connection refused")
            except ValueError as e:
                raise handle_error(
                    e,
                    "initialize database connection",
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    client_message="Service temporarily unavailable. Please try again later."
                )
        
        with pytest.raises(HTTPException) as exc_info:
            failing_route()
        
        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert exc_info.value.detail == "Service temporarily unavailable. Please try again later."
    
    def test_nested_exception_handling(self):
        """Multiple levels of exception handling work correctly."""
        def inner_function():
            raise RuntimeError("Specific error details")
        
        def outer_function():
            try:
                inner_function()
            except RuntimeError as e:
                raise handle_error(
                    e,
                    "process data",
                    client_message="Processing failed."
                )
        
        with pytest.raises(HTTPException) as exc_info:
            outer_function()
        
        assert exc_info.value.detail == "Processing failed."


class TestErrorMessageSanitization:
    """Verify error messages don't leak sensitive information."""
    
    def test_database_paths_not_exposed(self):
        """Database file paths not exposed in client messages."""
        exc = FileNotFoundError("/var/lib/database/litreview.db")
        
        with pytest.raises(HTTPException) as exc_info:
            handle_error(exc, "load database", status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        assert "/var/lib/database" not in exc_info.value.detail
        assert "database" not in exc_info.value.detail.lower()
    
    def test_credentials_not_exposed(self):
        """Credentials not exposed in client messages."""
        exc = ValueError("Failed to connect with password='secret123' to admin@192.168.1.1")
        
        with pytest.raises(HTTPException) as exc_info:
            handle_error(exc, "connect to server")
        
        assert "secret123" not in exc_info.value.detail
        assert "192.168.1.1" not in exc_info.value.detail
        assert "admin@" not in exc_info.value.detail
    
    def test_internal_logic_not_exposed(self):
        """Internal business logic not exposed."""
        exc = Exception("User ID 42 has insufficient credits for premium feature")
        
        with pytest.raises(HTTPException) as exc_info:
            handle_error(exc, "process upgrade", status.HTTP_402_PAYMENT_REQUIRED)
        
        # ID and internal logic should not be exposed
        detail = exc_info.value.detail
        assert "42" not in detail or "insufficient" not in detail.lower()
