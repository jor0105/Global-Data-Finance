import importlib

import pytest
from pydantic import ValidationError


def test_defaults_imported_settings():
    from globaldatafinance.core import config

    settings = config.settings

    assert settings.network.timeout == 300
    assert settings.network.max_retries == 3
    assert settings.network.retry_backoff == 1.0

    assert settings.debug is False


def test_env_overrides_reflect_after_reload(monkeypatch):
    monkeypatch.setenv("DATAFINANCE_NETWORK_TIMEOUT", "60")

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

        assert hasattr(config.settings, "debug")
        assert isinstance(config.settings.debug, bool)

    def test_scenarios_network_user_agent(self):
        from globaldatafinance.core import config

        assert isinstance(config.settings.network.user_agent, str)
        assert "Global-Data-Finance" in config.settings.network.user_agent

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


def test_extra_fields_in_env_file_are_ignored(tmp_path, monkeypatch):
    """Test that Settings class ignores extra fields without validation errors.

    This test simulates the real-world scenario where users have .env files
    with variables for other projects (e.g., openai_api_key from other tools).
    """
    from globaldatafinance.core.config import Settings

    # Create a temporary .env file with both valid and extra fields
    env_file = tmp_path / ".env"
    env_file.write_text(
        "openai_api_key=sk-proj-test123\n"
        "some_random_var=value\n"
        "another_extra_field=12345\n"
    )

    # Change to the directory with the .env file
    monkeypatch.chdir(tmp_path)

    # The key test: this should NOT raise ValidationError despite extra fields
    try:
        settings = Settings()
        # If we got here, the test passed - extra fields were ignored
        assert True
    except Exception as e:
        # If we get a validation error about extra fields, the fix didn't work
        if "Extra inputs are not permitted" in str(e):
            pytest.fail(f"Settings rejected extra fields in .env file: {e}")
        else:
            # Some other error, re-raise it
            raise

    # Verify that extra fields are not accessible on the settings object
    assert not hasattr(settings, "openai_api_key")
    assert not hasattr(settings, "some_random_var")
