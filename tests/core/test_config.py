import importlib

import pytest
from pydantic import ValidationError


def test_defaults_imported_settings():
    from datafinance.core import config

    settings = config.settings

    assert settings.network.timeout == 300
    assert settings.network.max_retries == 3
    assert settings.network.retry_backoff == 1.0

    assert settings.debug is False


def test_env_overrides_reflect_after_reload(monkeypatch):
    monkeypatch.setenv("DATAFINANCE_NETWORK_TIMEOUT", "60")

    from datafinance.core import config as cfg_mod

    importlib.reload(cfg_mod)

    settings = cfg_mod.settings
    assert settings.network.timeout == 60


def test_network_settings_bounds_validation():
    from datafinance.core.config import NetworkSettings

    with pytest.raises(ValidationError):
        NetworkSettings(timeout=10)

    with pytest.raises(ValidationError):
        NetworkSettings(max_retries=999)


@pytest.mark.unit
class TestSettingsScenarios:
    def test_scenarios_debug_flag(self):
        from datafinance.core import config
        assert hasattr(config.settings, "debug")
        assert isinstance(config.settings.debug, bool)

    def test_scenarios_network_user_agent(self):
        from datafinance.core import config
        assert isinstance(config.settings.network.user_agent, str)
        assert "DataFinance" in config.settings.network.user_agent

    def test_scenarios_network_retry_backoff_bounds(self):
        from datafinance.core.config import NetworkSettings
        with pytest.raises(ValidationError):
            NetworkSettings(retry_backoff=0.05)
        with pytest.raises(ValidationError):
            NetworkSettings(retry_backoff=20.0)

    def test_scenarios_network_max_retries_bounds(self):
        from datafinance.core.config import NetworkSettings
        with pytest.raises(ValidationError):
            NetworkSettings(max_retries=-1)
        with pytest.raises(ValidationError):
            NetworkSettings(max_retries=11)

    def test_scenarios_network_timeout_bounds(self):
        from datafinance.core.config import NetworkSettings
        with pytest.raises(ValidationError):
            NetworkSettings(timeout=5)
        with pytest.raises(ValidationError):
            NetworkSettings(timeout=4000)
