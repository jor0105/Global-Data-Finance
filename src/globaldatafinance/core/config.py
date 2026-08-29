"""Centralized configuration module for global Global-Data-Finance settings.

This module provides type-safe, validated configuration management
with support for environment variables and default values.

ONLY contains truly global configurations that apply across all data sources
(CVM, B3, SEC, etc.). Source-specific configs remain in their respective
domains.

Note: For logging configuration, use the
globaldatafinance.core.logging_config module directly.

Example:
    >>> from globaldatafinance.core.config import settings
    >>> print(settings.network.timeout)
    180
    >>> # Override via environment variable
    >>> # export DATAFINANCE_NETWORK_TIMEOUT=600
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NetworkSettings(BaseSettings):
    """Global network configuration for HTTP requests."""

    timeout: int = Field(
        default=180,
        ge=30,
        le=3600,
        description='Default timeout for HTTP requests in seconds',
    )

    max_retries: int = Field(
        default=5,
        ge=0,
        le=10,
        description=(
            'Maximum number of additional retry attempts after the first '
            'request'
        ),
    )

    retry_backoff: float = Field(
        default=2.0,
        ge=0.1,
        le=10.0,
        description='Backoff multiplier for retries (exponential backoff)',
    )

    user_agent: str | None = Field(
        default=None,
        description='Optional user agent header for HTTP requests',
    )

    model_config = SettingsConfigDict(
        env_prefix='DATAFINANCE_NETWORK_',
        case_sensitive=False,
        extra='ignore',
    )


class Settings(BaseSettings):
    """Main settings container for global configurations.

    Contains only truly global settings. Source-specific configurations
    (CVM, B3, SEC) remain in their respective domain modules.

    Note: Logging configuration has moved to
    globaldatafinance.core.logging_config.
    """

    network: NetworkSettings = Field(default_factory=NetworkSettings)

    debug: bool = Field(
        default=False, description='Enable debug mode globally'
    )

    model_config = SettingsConfigDict(
        env_prefix='DATAFINANCE_',
        case_sensitive=False,
        extra='ignore',
    )


# Singleton instance
settings = Settings()
