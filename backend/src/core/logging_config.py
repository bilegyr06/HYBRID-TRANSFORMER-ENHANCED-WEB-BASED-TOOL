"""
Centralized logging configuration for the entire application.

Provides:
- Standardized log format with context (timestamp, level, logger, message)
- Separate handlers for console and file output
- Different log levels for development vs production
- Context enrichment (request ID, user ID, operation)
- Security logging for auth events
- Performance logging for slow operations

Usage:
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Operation completed", extra={"duration_ms": 150})
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any
from src.core.config import settings


# Create logs directory
LOGS_DIR = Path("data/logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def get_logging_config() -> Dict[str, Any]:
    """
    Get logging configuration dictionary for logging.config.dictConfig.
    
    Returns:
        Dictionary with logging configuration based on environment.
    """
    # Determine log level based on environment
    log_level = "DEBUG" if settings.ENVIRONMENT != "production" else "INFO"
    
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": (
                    "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | "
                    "%(funcName)s() | %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "fmt": "%(timestamp)s %(level)s %(name)s %(message)s",
            } if _try_import_json_logger() else None,
        },
        "filters": {
            "security_events": {
                "()": SecurityEventFilter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard" if settings.ENVIRONMENT == "production" else "detailed",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": LOGS_DIR / "app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "security_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "WARNING",
                "formatter": "detailed",
                "filename": LOGS_DIR / "security.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "filters": ["security_events"],
                "encoding": "utf-8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": LOGS_DIR / "errors.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
        },
        "loggers": {
            # Root logger
            "": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
            },
            # Application loggers
            "src": {
                "level": log_level,
                "handlers": ["console", "file", "error_file", "security_file"],
                "propagate": False,
            },
            # Auth-specific logging
            "src.services.auth_service": {
                "level": log_level,
                "handlers": ["console", "file", "security_file"],
                "propagate": False,
            },
            # Summarizer service logging
            "src.services.summarizer_service": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            # Database logging
            "src.core.database": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            # API logging
            "src.api": {
                "level": log_level,
                "handlers": ["console", "file", "security_file"],
                "propagate": False,
            },
            # FastAPI/Starlette
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            # SQLAlchemy (reduce verbosity)
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["file"],
                "propagate": False,
            },
        }
    }


class SecurityEventFilter(logging.Filter):
    """
    Filter for security-related events.
    
    Marks events that represent security concerns:
    - Authentication failures
    - Authorization denials
    - Rate limit violations
    - Path traversal attempts
    - Credential issues
    """
    
    SECURITY_KEYWORDS = [
        "auth", "unauthorized", "forbidden", "permission",
        "password", "credential", "jwt", "token",
        "rate limit", "attempt", "attack", "security",
        "traversal", "injection", "malicious"
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Mark record if it contains security keywords.
        
        Args:
            record: Log record to filter
            
        Returns:
            True (always pass through, but mark if security-related)
        """
        message = record.getMessage().lower()
        record.is_security_event = any(
            keyword in message
            for keyword in self.SECURITY_KEYWORDS
        )
        return True


def setup_logging() -> None:
    """
    Configure logging for the entire application.
    
    Must be called on application startup before logging is used.
    
    Usage:
        from src.core.logging_config import setup_logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("App started")
    """
    config = get_logging_config()
    
    # Remove json formatter if json logger not available
    if config["formatters"]["json"] is None:
        del config["formatters"]["json"]
    
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Convenience function - equivalent to logging.getLogger(name).
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        Logger instance with centralized configuration
        
    Example:
        logger = get_logger(__name__)
        logger.info("Operation completed")
    """
    return logging.getLogger(name)


def _try_import_json_logger() -> bool:
    """Try to import json logger library."""
    try:
        import pythonjsonlogger
        return True
    except ImportError:
        return False


# Context-aware logging helpers

class LogContext:
    """Context manager for adding context to logs."""
    
    def __init__(self, logger: logging.Logger, **context):
        """
        Create context for logging.
        
        Args:
            logger: Logger instance
            **context: Context key-value pairs
            
        Example:
            with LogContext(logger, user_id=123, action="delete"):
                logger.info("Action performed")  # Includes context
        """
        self.logger = logger
        self.context = context
        self.original_context = {}
    
    def __enter__(self):
        """Enter context and set extra fields."""
        # Store original values
        for key in self.context:
            self.original_context[key] = self.logger.__dict__.get(key)
        
        # Set new context
        for key, value in self.context.items():
            self.logger.__dict__[key] = value
        
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore original values."""
        for key, original_value in self.original_context.items():
            if original_value is None:
                self.logger.__dict__.pop(key, None)
            else:
                self.logger.__dict__[key] = original_value


# Performance logging helper

class log_performance:
    """Decorator to log function performance (duration)."""
    
    def __init__(self, logger: logging.Logger, threshold_ms: float = 1000):
        """
        Initialize performance logger.
        
        Args:
            logger: Logger instance
            threshold_ms: Log if duration exceeds this (milliseconds)
            
        Example:
            @log_performance(logger, threshold_ms=500)
            def slow_operation():
                # Logged if takes > 500ms
                pass
        """
        self.logger = logger
        self.threshold_ms = threshold_ms
    
    def __call__(self, func):
        """Wrap function with performance logging."""
        import functools
        import time
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start) * 1000
                if duration_ms > self.threshold_ms:
                    self.logger.info(
                        f"{func.__name__} took {duration_ms:.1f}ms",
                        extra={"duration_ms": duration_ms}
                    )
        
        return wrapper
