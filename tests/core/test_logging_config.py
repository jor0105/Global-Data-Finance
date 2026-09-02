import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import globaldatafinance.core.logging_config as logging_config_module
from globaldatafinance.core.logging_config import (
    StructuredFormatter,
    get_logger,
    get_logging_settings,
    is_logging_configured,
    log_execution_time,
    log_with_context,
    setup_logging,
)
from globaldatafinance.core.utils.files import remove_file

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def restore_logging_state():
    """Restore root handlers and library logging state after each test."""
    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level
    original_configured = logging_config_module._logging_configured
    original_settings = logging_config_module.get_logging_settings()
    original_settings = original_settings.model_copy(deep=True)

    yield

    for handler in list(root_logger.handlers):
        if handler not in original_handlers:
            root_logger.removeHandler(handler)
            handler.close()
    root_logger.handlers[:] = original_handlers
    root_logger.setLevel(original_level)
    logging_config_module._settings = original_settings
    logging_config_module._logging_configured = original_configured


class TestLoggingConfiguration:
    def test_get_logger_returns_logger(self):
        logger = get_logger('test_module')

        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test_module'

    def test_setup_logging_creates_handlers(self):
        setup_logging(level='INFO')
        root_logger = logging.getLogger()

        assert len(root_logger.handlers) > 0
        assert root_logger.level == logging.INFO

    def test_setup_logging_with_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'test.log'

            setup_logging(level='DEBUG', log_file=log_file)
            logger = get_logger('test_module')

            logger.debug('Debug message')
            logger.info('Info message')

            assert log_file.exists()
            content = log_file.read_text()
            assert 'Debug message' in content
            assert 'Info message' in content

    def test_log_with_context_emits_context_and_level(self, caplog):
        logger = get_logger('test_module')

        with caplog.at_level(logging.INFO, logger='test_module'):
            log_with_context(
                logger,
                'warning',
                'Processing file',
                file_path='data.csv',
                records=1000,
            )

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelno == logging.WARNING
        assert record.message == 'Processing file'
        assert record.file_path == 'data.csv'
        assert record.records == 1000

    def test_structured_formatter_renders_extra_data_and_safe_context(self):
        formatter = StructuredFormatter('%(message)s')
        record = logging.LogRecord(
            name='test_module',
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg='Processing file',
            args=(),
            exc_info=None,
        )
        record.extra_data = {'phase': 'download'}
        record.file_target = 'COTAHIST_A2023.ZIP'

        formatted = formatter.format(record)

        assert formatted.startswith('Processing file')
        assert 'phase=download' in formatted
        assert 'file_target=COTAHIST_A2023.ZIP' in formatted

    def test_filename_remains_reserved_by_standard_logging(self):
        logger = get_logger('test_reserved_logrecord_attribute')
        original_level = logger.level
        logger.setLevel(logging.INFO)

        try:
            with pytest.raises(KeyError, match='filename'):
                logger.info('Invalid context', extra={'filename': 'data.csv'})
        finally:
            logger.setLevel(original_level)

    @patch(
        'globaldatafinance.core.logging_config.time.perf_counter',
        side_effect=[10.0, 12.5],
    )
    def test_log_execution_time_success_emits_timing(
        self, mock_perf_counter, caplog
    ):
        logger = get_logger('test_module')

        with (
            caplog.at_level(logging.INFO, logger='test_module'),
            log_execution_time(logger, 'Test operation', file_path='data.csv'),
        ):
            pass

        assert mock_perf_counter.call_count == 2
        assert [record.message for record in caplog.records] == [
            'Starting: Test operation',
            'Completed: Test operation',
        ]
        completed = caplog.records[-1]
        assert completed.levelno == logging.INFO
        assert completed.operation == 'Test operation'
        assert completed.elapsed_seconds == '2.50'
        assert completed.file_path == 'data.csv'

    @patch(
        'globaldatafinance.core.logging_config.time.perf_counter',
        side_effect=[10.0, 11.25],
    )
    def test_log_execution_time_failure_emits_error_and_reraises(
        self, _mock_perf_counter, caplog
    ):
        logger = get_logger('test_module')

        with (
            caplog.at_level(logging.INFO, logger='test_module'),
            pytest.raises(ValueError, match='Test error'),
            log_execution_time(logger, 'Failing operation'),
        ):
            raise ValueError('Test error')

        failed = caplog.records[-1]
        assert failed.levelno == logging.ERROR
        assert failed.message == 'Failed: Failing operation'
        assert failed.operation == 'Failing operation'
        assert failed.elapsed_seconds == '1.25'
        assert failed.error == 'Test error'

    def test_different_log_levels_emit_exact_levels(self, caplog):
        logger = get_logger('test_module')

        with caplog.at_level(logging.DEBUG, logger='test_module'):
            logger.debug('Debug message')
            logger.info('Info message')
            logger.warning('Warning message')
            logger.error('Error message')

        assert [record.levelno for record in caplog.records] == [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
        ]
        assert [record.message for record in caplog.records] == [
            'Debug message',
            'Info message',
            'Warning message',
            'Error message',
        ]

    def test_log_execution_time_success_body_is_observed(self, caplog):
        logger = get_logger('test_module')

        with (
            caplog.at_level(logging.INFO, logger='test_module'),
            log_execution_time(logger, 'Observed operation'),
        ):
            logger.info('operation body')

        assert any(
            record.message == 'operation body' for record in caplog.records
        )

    def test_setup_logging_with_detailed_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'detailed.log'

            setup_logging(
                level='DEBUG', log_file=log_file, use_detailed_format=True
            )
            logger = get_logger('test_module')

            logger.info('Test with detailed format')

            content = log_file.read_text()
            assert 'test_setup_logging_with_detailed_format' in content

    def test_remove_file_removes_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / 'to_remove.txt'
            file_path.write_text('test')
            assert file_path.exists()
            remove_file(str(file_path))
            assert not file_path.exists()

    def test_remove_file_nonexistent_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / 'does_not_exist.txt'
            remove_file(str(file_path))
            assert not file_path.exists()

    def test_remove_file_logs_permission_failure_without_raising(
        self, tmp_path, monkeypatch, caplog
    ):
        file_path = tmp_path / 'protected.txt'
        file_path.write_text('content')

        def deny_unlink(_path: Path) -> None:
            raise PermissionError('permission denied')

        monkeypatch.setattr(Path, 'unlink', deny_unlink)

        with caplog.at_level(logging.WARNING):
            remove_file(str(file_path))

        assert file_path.exists()
        assert any(
            record.exc_info is not None
            and 'Failed to remove file' in record.message
            for record in caplog.records
        )

    def test_setup_logging_marks_configuration_and_applies_level(
        self, monkeypatch
    ):
        root_logger = logging.getLogger()
        monkeypatch.setattr(
            logging_config_module, '_logging_configured', False
        )

        assert is_logging_configured() is False

        setup_logging(level='WARNING')

        console_handlers = [
            handler
            for handler in root_logger.handlers
            if type(handler) is logging.StreamHandler
        ]
        assert is_logging_configured() is True
        assert get_logging_settings().level == 'WARNING'
        assert root_logger.level == logging.WARNING
        assert len(console_handlers) == 1
        assert console_handlers[0].level == logging.WARNING
