import importlib

import pytest
from pydantic import ValidationError


def test_defaults_imported_settings():
    from globaldatafinance.core import config

    settings = config.settings

    assert settings.network.timeout == 180
    assert settings.network.max_retries == 5
    assert settings.network.retry_backoff == 2.0
    assert settings.network.user_agent is None

    assert settings.debug is False


def test_env_overrides_reflect_after_reload(monkeypatch):
    monkeypatch.setenv('DATAFINANCE_NETWORK_TIMEOUT', '60')

    from globaldatafinance.core import config as cfg_mod

    importlib.reload(cfg_mod)

    settings = cfg_mod.settings
    assert settings.network.timeout == 60


def test_network_settings_bounds_validation():
    from globaldatafinance.core.config import NetworkSettings

    with pytest.raises(ValidationError):
        NetworkSettings(timeout=10)

    with pytest.raises(ValidationError):
        NetworkSettings(max_retries=999)


@pytest.mark.unit
class TestSettingsScenarios:
    def test_scenarios_debug_flag(self):
        from globaldatafinance.core import config

        assert hasattr(config.settings, 'debug')
        assert isinstance(config.settings.debug, bool)

    def test_scenarios_network_user_agent(self):
        from globaldatafinance.core import config

        assert config.settings.network.user_agent is None

    def test_scenarios_network_user_agent_can_be_configured(self, monkeypatch):
        from globaldatafinance.core.config import NetworkSettings

        monkeypatch.setenv('DATAFINANCE_NETWORK_USER_AGENT', 'test-client/1.0')

        configured = NetworkSettings()

        assert configured.user_agent == 'test-client/1.0'

    def test_scenarios_network_retry_backoff_bounds(self):
        from globaldatafinance.core.config import NetworkSettings

        with pytest.raises(ValidationError):
            NetworkSettings(retry_backoff=0.05)
        with pytest.raises(ValidationError):
            NetworkSettings(retry_backoff=20.0)

    def test_scenarios_network_max_retries_bounds(self):
        from globaldatafinance.core.config import NetworkSettings

        with pytest.raises(ValidationError):
            NetworkSettings(max_retries=-1)
        with pytest.raises(ValidationError):
            NetworkSettings(max_retries=11)

    def test_scenarios_network_timeout_bounds(self):
        from globaldatafinance.core.config import NetworkSettings

        with pytest.raises(ValidationError):
            NetworkSettings(timeout=5)
        with pytest.raises(ValidationError):
            NetworkSettings(timeout=4000)


def test_settings_does_not_load_dotenv_implicitly(tmp_path, monkeypatch):
    """Settings must ignore a working-directory dotenv unless requested."""
    from globaldatafinance.core.config import Settings

    env_file = tmp_path / '.env'
    env_file.write_text(
        'DATAFINANCE_DEBUG=true\n'
        'DATAFINANCE_NETWORK_TIMEOUT=60\n'
        'unrelated_setting=value\n'
    )

    monkeypatch.chdir(tmp_path)
    for name in (
        'DATAFINANCE_DEBUG',
        'DATAFINANCE_NETWORK',
        'DATAFINANCE_NETWORK_TIMEOUT',
        'DATAFINANCE_NETWORK_MAX_RETRIES',
        'DATAFINANCE_NETWORK_RETRY_BACKOFF',
        'DATAFINANCE_NETWORK_USER_AGENT',
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings()

    assert settings.network.timeout == 180
    assert settings.debug is False
    assert Settings.model_config.get('env_file') is None
    assert Settings.model_config.get('env_file_encoding') is None


def test_settings_loads_dotenv_when_requested_explicitly(
    tmp_path, monkeypatch
):
    """Settings must support pydantic-settings' explicit dotenv override."""
    from globaldatafinance.core.config import Settings

    env_file = tmp_path / 'explicit.env'
    env_file.write_text(
        'DATAFINANCE_DEBUG=true\n'
        'DATAFINANCE_NETWORK={"timeout": 240, "max_retries": 4}\n',
        encoding='utf-8',
    )

    for name in (
        'DATAFINANCE_DEBUG',
        'DATAFINANCE_NETWORK',
        'DATAFINANCE_NETWORK_TIMEOUT',
        'DATAFINANCE_NETWORK_MAX_RETRIES',
        'DATAFINANCE_NETWORK_RETRY_BACKOFF',
        'DATAFINANCE_NETWORK_USER_AGENT',
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=env_file)

    assert settings.debug is True
    assert settings.network.timeout == 240
    assert settings.network.max_retries == 4
