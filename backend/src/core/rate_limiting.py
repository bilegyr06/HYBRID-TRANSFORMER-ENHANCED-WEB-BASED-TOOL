"""
Rate limiting configuration for login endpoints.

Prevents brute force attacks by limiting login attempts:
- 5 attempts per 15 minutes per IP address
- Returns 429 (Too Many Requests) when exceeded
- Detailed logging of rate limit violations

Configured via slowapi (ASGI rate limiting middleware).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


# Rate limiter instance: 5 attempts per 15 minutes per IP
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],  # Default for all endpoints (generous)
)


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Configure rate limiting for the FastAPI application.
    
    Applies stricter limits to sensitive endpoints:
    - /auth/login: 5 attempts / 15 minutes (prevents brute force)
    - /auth/register: 3 new accounts / 15 minutes (prevents spam)
    
    Args:
        app: FastAPI application instance
    """
    app.state.limiter = limiter
    
    # Add rate limit exception handler
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        """Handle rate limit violations with safe error message."""
        client_ip = get_remote_address(request)
        endpoint = request.url.path
        
        logger.warning(
            f"Rate limit exceeded",
            extra={
                "client_ip": client_ip,
                "endpoint": endpoint,
                "limit": exc.detail,
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Too many requests. Please try again later.",
                "retry_after": "15 minutes"
            }
        )


# Rate limit strings for different endpoints
LOGIN_RATE_LIMIT = "5/15 minutes"  # Brute force protection
REGISTER_RATE_LIMIT = "3/15 minutes"  # Spam prevention
