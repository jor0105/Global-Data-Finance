import importlib
import logging
from pathlib import Path

import pytest
from pydantic import ValidationError


def test_defaults_imported_settings():
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
    monkeypatch.setenv("DATAFIN_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DATAFIN_NETWORK_TIMEOUT", "60")
    from src.core import config as cfg_mod

    importlib.reload(cfg_mod)
    settings = cfg_mod.settings
    assert settings.logging.level == "DEBUG"
    assert settings.network.timeout == 60


def test_logging_level_validation_and_uppercase():
    from src.core.config import LoggingSettings

    ls = LoggingSettings(level="debug")
    assert ls.level == "DEBUG"
    with pytest.raises(ValidationError):
        LoggingSettings(level="NOT_A_LEVEL")


def test_network_settings_bounds_validation():
    from src.core.config import NetworkSettings

    with pytest.raises(ValidationError):
        NetworkSettings(timeout=10)
    with pytest.raises(ValidationError):
        NetworkSettings(max_retries=999)


def test_configure_logging_filehandler_and_debug(tmp_path):
    from src.core.config import LoggingSettings, NetworkSettings, Settings

    log_file = tmp_path / "my_test.log"
    s = Settings(
        logging=LoggingSettings(level="INFO", log_file=str(log_file)),
        network=NetworkSettings(),
        debug=True,
    )
    for h in logging.root.handlers[:]:
        logging.root.removeHandler(h)
    s.configure_logging()
    handlers = logging.root.handlers
    assert any(
        isinstance(h, logging.FileHandler)
        and Path(getattr(h, "baseFilename", "")).name == log_file.name
        for h in handlers
    )
    assert logging.getLogger("src").level == logging.DEBUG
    for h in logging.root.handlers[:]:
        logging.root.removeHandler(h)
