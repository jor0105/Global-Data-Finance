"""Centralized logging configuration for DataFinance library.

This module provides a unified, production-ready logging system with:
- Lazy initialization (logging disabled by default)
- Console and file handlers
- Customizable log levels
- Performance timing utilities
- Context-aware structured logging
- Environment variable support

Architecture:
    - setup_logging(): Initialize logging (call once at application start)
    - get_logger(): Get logger instance for any module
    - log_execution_time(): Context manager for timing operations
    - Automatic log formatting with structured data

Usage:
    Basic usage:
        >>> from src.core.logging_config import setup_logging, get_logger
        >>>
        >>> # Enable logging at application start
        >>> setup_logging(level="INFO")
        >>>
        >>> # Get logger in any module
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started", extra={"file_count": 10})

    Performance timing:
        >>> from src.core.logging_config import log_execution_time, get_logger
        >>>
        >>> logger = get_logger(__name__)
        >>> with log_execution_time(logger, "Download files", total=100):
        ...     download_files()

    Environment variables:
        >>> # Set via environment
        >>> # export DATAFIN_LOG_LEVEL=DEBUG
        >>> # export DATAFIN_LOG_FILE=/var/log/datafin.log
        >>> # export DATAFIN_LOG_STRUCTURED=true
        >>>
        >>> # Or programmatically
        >>> setup_logging(level="DEBUG", log_file="/tmp/datafin.log")

Design principles:
    - Logging is DISABLED by default (library-friendly)
    - Users must explicitly call setup_logging() to enable logs
    - All modules use get_logger(__name__) for consistent naming
    - Structured logging via 'extra' parameter
    - No auto-configuration on import
"""

import logging
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

# ============================================================================
# LOG FORMATS
# ============================================================================

DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DETAILED_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ============================================================================
# SETTINGS
# ============================================================================


class LoggingSettings(BaseSettings):
    """Global logging configuration with environment variable support."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Global logging level"
    )

    format: str = Field(
        default=DEFAULT_FORMAT,
        description="Log message format",
    )

    log_file: Optional[str] = Field(
        default=None, description="Path to log file (None = console only)"
    )

    structured: bool = Field(
        default=False, description="Enable structured logging (JSON format)"
    )

    detailed_format: bool = Field(
        default=False, description="Include line numbers and function names"
    )

    class Config:
        """Pydantic configuration."""

        env_prefix = "DATAFIN_LOG_"
        case_sensitive = False

    @field_validator("level", mode="before")
    @classmethod
    def validate_level(cls, v):
        """Normalize logging level to uppercase."""
        if v is None:
            return v
        if isinstance(v, str):
            return v.upper()
        return v


# Global settings instance
_settings = LoggingSettings()
_logging_configured = False


# ============================================================================
# FORMATTERS & FILTERS
# ============================================================================


class ContextFilter(logging.Filter):
    """Add contextual information to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add custom fields to log record if not present."""
        if not hasattr(record, "extra_data"):
            record.extra_data = {}
        return True


class StructuredFormatter(logging.Formatter):
    """Custom formatter that handles extra data from log calls."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with extra data if present."""
        message = super().format(record)

        # Add extra data if present
        extra_data = getattr(record, "extra_data", {})
        if extra_data:
            extra_str = " | ".join(f"{k}={v}" for k, v in extra_data.items())
            message = f"{message} | {extra_str}"

        return message


# ============================================================================
# CORE FUNCTIONS
# ============================================================================


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    structured: bool = False,
    use_detailed_format: bool = False,
) -> None:
    """Setup logging for DataFinance library.

    Call this function at application start if you want to see log messages.
    By default, logging is disabled to keep your application clean.

    This function configures the root logger and can be called multiple times
    to reconfigure logging (e.g., to change level or add file handler).

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               If None, uses DATAFIN_LOG_LEVEL env var or defaults to INFO.
        log_file: Path to log file. If None, logs go to console only.
        structured: Enable JSON structured logging (not yet implemented).
        use_detailed_format: If True, includes line numbers and function names.

    Example:
        >>> from src.core.logging_config import setup_logging
        >>>
        >>> # Basic setup
        >>> setup_logging(level="INFO")
        >>>
        >>> # With file output
        >>> setup_logging(level="DEBUG", log_file="/tmp/datafin.log")
        >>>
        >>> # Detailed format for debugging
        >>> setup_logging(level="DEBUG", use_detailed_format=True)
    """
    global _logging_configured, _settings

    # Update settings if parameters provided
    if level:
        normalized = level.upper() if isinstance(level, str) else level
        _settings.level = normalized  # type: ignore
    if log_file:
        _settings.log_file = log_file
    if structured:
        _settings.structured = structured
    if use_detailed_format:
        _settings.detailed_format = use_detailed_format

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, _settings.level))

    # Clear any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Choose format
    log_format = DETAILED_FORMAT if _settings.detailed_format else DEFAULT_FORMAT

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, _settings.level))
    console_formatter = StructuredFormatter(log_format, datefmt=DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(ContextFilter())
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if _settings.log_file:
        log_file_path = Path(_settings.log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(getattr(logging, _settings.level))
        file_formatter = StructuredFormatter(DETAILED_FORMAT, datefmt=DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(ContextFilter())
        root_logger.addHandler(file_handler)

    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module.

    This is the standard way to get a logger in any module.
    Always use __name__ as the logger name for proper hierarchical naming.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Configured logger instance

    Example:
        >>> from src.core.logging_config import get_logger
        >>>
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing file", extra={"filename": "data.csv"})
        >>> logger.debug("Record count", extra={"count": 1000})
    """
    return logging.getLogger(name)


@contextmanager
def log_execution_time(logger: logging.Logger, operation: str, **context: Any):
    """Context manager to log execution time of operations.

    Logs the start of the operation, measures execution time, and logs
    completion with elapsed time. If an exception occurs, logs the error
    with execution time and re-raises.

    Args:
        logger: Logger instance to use
        operation: Description of the operation being timed
        **context: Additional context to include in logs

    Yields:
        None

    Example:
        >>> from src.core.logging_config import log_execution_time, get_logger
        >>>
        >>> logger = get_logger(__name__)
        >>> with log_execution_time(logger, "Parse ZIP file", filename="data.zip"):
        ...     parse_file()
        ...
        >>> # Output:
        >>> # Starting: Parse ZIP file | operation=Parse ZIP file | filename=data.zip
        >>> # Completed: Parse ZIP file | operation=Parse ZIP file | elapsed_seconds=2.45 | filename=data.zip
    """
    start_time = time.perf_counter()
    logger.info(
        f"Starting: {operation}",
        extra={"operation": operation, **context},
    )

    try:
        yield
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        logger.error(
            f"Failed: {operation}",
            extra={
                "operation": operation,
                "elapsed_seconds": f"{elapsed:.2f}",
                "error": str(e),
                **context,
            },
            exc_info=True,
        )
        raise
    else:
        elapsed = time.perf_counter() - start_time
        logger.info(
            f"Completed: {operation}",
            extra={
                "operation": operation,
                "elapsed_seconds": f"{elapsed:.2f}",
                **context,
            },
        )


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **context: Any,
) -> None:
    """Log a message with structured context data.

    Convenience function for logging with extra context fields.

    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **context: Additional context fields

    Example:
        >>> from src.core.logging_config import log_with_context, get_logger
        >>>
        >>> logger = get_logger(__name__)
        >>> log_with_context(
        ...     logger,
        ...     "info",
        ...     "File processed successfully",
        ...     filename="data.csv",
        ...     records=1000,
        ...     elapsed_ms=250
        ... )
    """
    log_method = getattr(logger, level.lower())
    log_method(message, extra=context)


def is_logging_configured() -> bool:
    """Check if logging has been configured.

    Returns:
        True if setup_logging() has been called, False otherwise

    Example:
        >>> from src.core.logging_config import is_logging_configured, setup_logging
        >>>
        >>> if not is_logging_configured():
        ...     setup_logging(level="INFO")
    """
    return _logging_configured


def get_logging_settings() -> LoggingSettings:
    """Get current logging settings.

    Returns:
        Current LoggingSettings instance

    Example:
        >>> from src.core.logging_config import get_logging_settings
        >>>
        >>> settings = get_logging_settings()
        >>> print(f"Current log level: {settings.level}")
    """
    return _settings


# ============================================================================
# UTILITY: File removal helper (moved from config.py)
# ============================================================================


def remove_file(filepath: str, log_on_error: bool = True) -> None:
    """Remove a file from disk safely.

    Utility function that removes any file from disk, with optional logging
    on errors. Handles missing files gracefully.

    Args:
        filepath: Path to the file to remove
        log_on_error: If True, logs warnings when file deletion fails

    Example:
        >>> from src.core.logging_config import remove_file
        >>>
        >>> remove_file("/path/to/file.zip")
    """
    logger = get_logger(__name__)
    try:
        path_obj = Path(filepath)
        if path_obj.exists():
            path_obj.unlink()
            logger.debug(f"Removed file: {filepath}")
    except Exception as e:
        if log_on_error:
            logger.warning(f"Failed to remove file {filepath}: {e}")
