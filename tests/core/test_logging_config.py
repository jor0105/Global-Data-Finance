import logging
import os
import tempfile
from pathlib import Path

import pytest

from globaldatafinance.core.logging_config import (
    get_logger,
    get_logging_settings,
    is_logging_configured,
    log_execution_time,
    log_with_context,
    remove_file,
    setup_logging,
)


class TestLoggingConfiguration:
    def test_get_logger_returns_logger(self):
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_setup_logging_creates_handlers(self):
        setup_logging(level="INFO")
        root_logger = logging.getLogger()

        assert len(root_logger.handlers) > 0
        assert root_logger.level == logging.INFO

    def test_setup_logging_with_file(self):
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
        logger = get_logger("test_module")

        log_with_context(
            logger, "info", "Processing file", file_path="data.csv", records=1000
        )

    def test_log_execution_time_success_executes(self):
        logger = get_logger("test_module")

        with log_execution_time(logger, "Test operation"):
            pass

    def test_log_execution_time_failure_raises(self):
        logger = get_logger("test_module")

        with pytest.raises(ValueError, match="Test error"):
            with log_execution_time(logger, "Failing operation"):
                raise ValueError("Test error")

    def test_different_log_levels_execute(self):
        logger = get_logger("test_module")

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

    def test_setup_logging_with_detailed_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "detailed.log"

            setup_logging(level="DEBUG", log_file=log_file, use_detailed_format=True)
            logger = get_logger("test_module")

            logger.info("Test with detailed format")

            content = log_file.read_text()
            assert "test_setup_logging_with_detailed_format" in content

    def test_remove_file_removes_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "to_remove.txt")
            with open(file_path, "w") as f:
                f.write("test")
            assert os.path.exists(file_path)
            remove_file(file_path)
            assert not os.path.exists(file_path)

    def test_remove_file_nonexistent_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "does_not_exist.txt")
            remove_file(file_path)
            assert not os.path.exists(file_path)

    def test_is_logging_configured_and_get_logging_settings(self):
        assert isinstance(is_logging_configured(), bool)
        settings = get_logging_settings()
        assert hasattr(settings, "level")
