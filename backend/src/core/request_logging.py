"""
Request/Response logging middleware (Phase 3.4).
Supporting feature: Centralized request/response tracking for debugging and monitoring.
"""
import time
import logging
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import uuid
from src.core.performance_metrics import get_metrics_instance

logger = logging.getLogger(__name__)


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.
    
    Tracks:
    - Request method, path, query parameters
    - Response status code and size
    - Execution time
    - Request size
    - User ID (if authenticated)
    - Errors and exceptions
    
    Each request is assigned a unique request ID for tracing.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log request/response details."""
        
        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract request details
        method = request.method
        path = request.url.path
        query_string = request.url.query
        
        # Extract client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Try to extract user ID from token if authenticated
        user_id = "anonymous"
        try:
            # Check for Bearer token in Authorization header
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                # Token is available, but we can't decode it here easily
                # It will be decoded by the actual endpoint
                user_id = "authenticated"
        except Exception:
            pass
        
        # Record request start time
        start_time = time.time()
        
        # Try to get request body size
        request_body_size = 0
        if method in ["POST", "PUT", "PATCH"]:
            try:
                content_length = request.headers.get("content-length")
                if content_length:
                    request_body_size = int(content_length)
            except (ValueError, TypeError):
                pass
        
        # Log incoming request
        logger.info(
            f"→ {method} {path}",
            extra={
                "request_id": request_id,
                "client_ip": client_ip,
                "user_id": user_id,
                "method": method,
                "path": path,
                "query_string": query_string,
                "request_size_bytes": request_body_size,
                "event_type": "request_received"
            }
        )
        
        # Process request and get response
        response_status = 500  # Default to server error
        response_size = 0
        error_occurred = False
        error_message = None
        
        try:
            response = await call_next(request)
            response_status = response.status_code
            
            # Try to get response size
            try:
                content_length = response.headers.get("content-length")
                if content_length:
                    response_size = int(content_length)
            except (ValueError, TypeError):
                pass
            
        except Exception as e:
            error_occurred = True
            error_message = str(e)
            logger.error(
                f"Exception during request processing: {error_message}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "event_type": "request_error"
                },
                exc_info=True
            )
            raise
        
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Record performance metrics (Phase 3.5)
        metrics = get_metrics_instance()
        metrics.record_request(
            path,
            method,
            execution_time_ms,
            error=error_occurred or response_status >= 500
        )
        
        # Determine log level based on status code
        if response_status < 300:
            log_level = "info"
            log_func = logger.info
        elif response_status < 400:
            log_level = "info"
            log_func = logger.info
        elif response_status < 500:
            log_level = "warning"
            log_func = logger.warning
        else:
            log_level = "error"
            log_func = logger.error
        
        # Log response
        log_func(
            f"← {method} {path} [{response_status}]",
            extra={
                "request_id": request_id,
                "client_ip": client_ip,
                "user_id": user_id,
                "method": method,
                "path": path,
                "status_code": response_status,
                "response_size_bytes": response_size,
                "execution_time_ms": round(execution_time_ms, 2),
                "total_size_bytes": request_body_size + response_size,
                "error_occurred": error_occurred,
                "event_type": "request_completed"
            }
        )
        
        # Add request ID to response headers for tracing
        response.headers["X-Request-ID"] = request_id
        
        return response


class SlowRequestWarningMiddleware(BaseHTTPMiddleware):
    """
    Middleware to warn about slow requests (Phase 3.5 performance monitoring).
    
    Logs warnings for requests exceeding threshold.
    """
    
    def __init__(self, app: ASGIApp, slow_request_threshold_ms: int = 1000):
        """
        Initialize slow request detection.
        
        Args:
            app: ASGI app
            slow_request_threshold_ms: Threshold for warning (default: 1000ms)
        """
        super().__init__(app)
        self.threshold_ms = slow_request_threshold_ms
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track and warn about slow requests."""
        start_time = time.time()
        
        try:
            response = await call_next(request)
        finally:
            execution_time_ms = (time.time() - start_time) * 1000
            
            if execution_time_ms > self.threshold_ms:
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} took {execution_time_ms:.2f}ms",
                    extra={
                        "request_id": getattr(request.state, "request_id", "unknown"),
                        "method": request.method,
                        "path": request.url.path,
                        "execution_time_ms": round(execution_time_ms, 2),
                        "threshold_ms": self.threshold_ms,
                        "event_type": "slow_request"
                    }
                )
        
        return response


def setup_request_logging(app, slow_request_threshold_ms: int = 1000):
    """
    Setup request/response logging middleware on FastAPI app.
    
    Args:
        app: FastAPI application instance
        slow_request_threshold_ms: Threshold for slow request warnings
    """
    app.add_middleware(SlowRequestWarningMiddleware, slow_request_threshold_ms=slow_request_threshold_ms)
    app.add_middleware(RequestResponseLoggingMiddleware)
    logger.info(
        f"Request/response logging middleware configured (slow threshold: {slow_request_threshold_ms}ms)"
    )
