import importlib
import logging
from pathlib import Path

import pytest
from pydantic import ValidationError


def test_defaults_imported_settings():
    # Import module (module-level singleton is created on import)
    from src.core import config

    settings = config.settings

    assert settings.logging.level == "INFO"
    assert settings.logging.format is not None
    assert settings.logging.log_file is None

    assert settings.network.timeout == 300
    assert settings.network.max_retries == 3
    assert settings.network.retry_backoff == 1.0

    assert settings.debug is False


def test_env_overrides_reflect_after_reload(monkeypatch):
    # Set environment variables and reload module so BaseSettings will pick them up
    monkeypatch.setenv("DATAFIN_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DATAFIN_NETWORK_TIMEOUT", "60")

    # import then reload
    from src.core import config as cfg_mod

    importlib.reload(cfg_mod)

    settings = cfg_mod.settings
    assert settings.logging.level == "DEBUG"
    assert settings.network.timeout == 60


def test_logging_level_validation_and_uppercase():
    from src.core.config import LoggingSettings

    # Lowercase should be coerced to uppercase by validator
    ls = LoggingSettings(level="debug")
    assert ls.level == "DEBUG"

    # Invalid literal should raise ValidationError
    with pytest.raises(ValidationError):
        LoggingSettings(level="NOT_A_LEVEL")


def test_network_settings_bounds_validation():
    from src.core.config import NetworkSettings

    # Below minimum should raise
    with pytest.raises(ValidationError):
        NetworkSettings(timeout=10)

    # Above maximum allowed for max_retries
    with pytest.raises(ValidationError):
        NetworkSettings(max_retries=999)


def test_configure_logging_filehandler_and_debug(tmp_path):
    # Create a temporary file path and custom Settings instance
    from src.core.config import LoggingSettings, NetworkSettings, Settings

    log_file = tmp_path / "my_test.log"

    s = Settings(
        logging=LoggingSettings(level="INFO", log_file=str(log_file)),
        network=NetworkSettings(),
        debug=True,
    )

    # Ensure a clean handlers list before configuration
    for h in logging.root.handlers[:]:
        logging.root.removeHandler(h)

    s.configure_logging()

    # There should be at least one FileHandler pointing to our file
    handlers = logging.root.handlers
    assert any(
        isinstance(h, logging.FileHandler)
        and Path(getattr(h, "baseFilename", "")).name == log_file.name
        for h in handlers
    )

    # When debug=True the `src` logger should be set to DEBUG
    assert logging.getLogger("src").level == logging.DEBUG

    # Cleanup handlers to avoid side-effects for other tests
    for h in logging.root.handlers[:]:
        logging.root.removeHandler(h)
