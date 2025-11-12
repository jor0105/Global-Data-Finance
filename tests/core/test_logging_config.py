"""Tests for logging configuration."""

import logging
import tempfile
from pathlib import Path

import pytest

from src.core.logging_config import (
    get_logger,
    log_execution_time,
    log_with_context,
    setup_logging,
)


class TestLoggingConfiguration:
    """Test suite for logging configuration."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_setup_logging_creates_handlers(self):
        """Test that setup_logging creates appropriate handlers."""
        setup_logging(level="INFO")
        root_logger = logging.getLogger()

        # Should have at least console handler
        assert len(root_logger.handlers) > 0
        assert root_logger.level == logging.INFO

    def test_setup_logging_with_file(self):
        """Test logging setup with file handler."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            setup_logging(level="DEBUG", log_file=log_file)
            logger = get_logger("test_module")

            logger.debug("Debug message")
            logger.info("Info message")

            assert log_file.exists()
            content = log_file.read_text()
            assert "Debug message" in content
            assert "Info message" in content

    def test_log_with_context_executes(self):
        """Test logging with structured context executes without error."""
        logger = get_logger("test_module")

        # Should not raise any exception (avoid reserved names like 'filename')
        log_with_context(
            logger, "info", "Processing file", file_path="data.csv", records=1000
        )

    def test_log_execution_time_success_executes(self):
        """Test execution time logging for successful operations."""
        logger = get_logger("test_module")

        # Should not raise any exception
        with log_execution_time(logger, "Test operation"):
            # Simulate some work
            pass

    def test_log_execution_time_failure_raises(self):
        """Test execution time logging for failed operations."""
        logger = get_logger("test_module")

        with pytest.raises(ValueError, match="Test error"):
            with log_execution_time(logger, "Failing operation"):
                raise ValueError("Test error")

    def test_different_log_levels_execute(self):
        """Test different log levels execute without error."""
        logger = get_logger("test_module")

        # Should not raise any exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

    def test_setup_logging_with_detailed_format(self):
        """Test logging with detailed format including line numbers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "detailed.log"

            setup_logging(level="DEBUG", log_file=log_file, use_detailed_format=True)
            logger = get_logger("test_module")

            logger.info("Test with detailed format")

            content = log_file.read_text()
            # Detailed format includes function name
            assert "test_setup_logging_with_detailed_format" in content
