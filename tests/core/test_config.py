import importlib

import pytest
from pydantic import ValidationError


def test_defaults_imported_settings():
    from src.core import config

    settings = config.settings

    assert settings.network.timeout == 300
    assert settings.network.max_retries == 3
    assert settings.network.retry_backoff == 1.0

    assert settings.debug is False


def test_env_overrides_reflect_after_reload(monkeypatch):
    monkeypatch.setenv("DATAFIN_NETWORK_TIMEOUT", "60")

    from src.core import config as cfg_mod

    importlib.reload(cfg_mod)

    settings = cfg_mod.settings
    assert settings.network.timeout == 60


def test_network_settings_bounds_validation():
    from src.core.config import NetworkSettings

    with pytest.raises(ValidationError):
        NetworkSettings(timeout=10)

    with pytest.raises(ValidationError):
        NetworkSettings(max_retries=999)
