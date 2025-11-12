import importlib

import pytest
from pydantic import ValidationError


def test_defaults_imported_settings():
    """Test that default settings are correctly loaded."""
    from src.core import config

    settings = config.settings

    # Logging configuration has been moved to logging_config.py
    # Test only network and debug settings
    assert settings.network.timeout == 300
    assert settings.network.max_retries == 3
    assert settings.network.retry_backoff == 1.0

    assert settings.debug is False


def test_env_overrides_reflect_after_reload(monkeypatch):
    """Test that environment variables override default settings."""
    # Set environment variable and reload module
    monkeypatch.setenv("DATAFIN_NETWORK_TIMEOUT", "60")

    # import then reload
    from src.core import config as cfg_mod

    importlib.reload(cfg_mod)

    settings = cfg_mod.settings
    assert settings.network.timeout == 60


def test_network_settings_bounds_validation():
    """Test that network settings validation works correctly."""
    from src.core.config import NetworkSettings

    # Below minimum should raise
    with pytest.raises(ValidationError):
        NetworkSettings(timeout=10)

    # Above maximum allowed for max_retries
    with pytest.raises(ValidationError):
        NetworkSettings(max_retries=999)
