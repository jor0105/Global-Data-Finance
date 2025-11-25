"""Centralized configuration module for global Global-Data-Finance settings.

This module provides type-safe, validated configuration management
with support for environment variables and default values.

ONLY contains truly global configurations that apply across all data sources
(CVM, B3, SEC, etc.). Source-specific configs remain in their respective domains.

Note: For logging configuration, use src.core.logging_config module directly.

Example:
    >>> from src.core.config import settings
    >>> print(settings.network.timeout)
    300
    >>> # Override via environment variable
    >>> # export DATAFIN_NETWORK_TIMEOUT=600
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class NetworkSettings(BaseSettings):
    """Global network configuration for HTTP requests."""

    timeout: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="Default timeout for HTTP requests in seconds",
    )

    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts for failed requests",
    )

    retry_backoff: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Backoff multiplier for retries (exponential backoff)",
    )

    user_agent: str = Field(
        default="Global-Data-Finance/1.0 (Python Financial Data Library)",
        description="User agent for HTTP requests",
    )

    class Config:
        """Network configuration class."""

        env_prefix = "DATAFINANCE_NETWORK_"
        case_sensitive = False


class Settings(BaseSettings):
    """Main settings container for global configurations.

    Contains only truly global settings. Source-specific configurations
    (CVM, B3, SEC) remain in their respective domain modules.

    Note: Logging configuration has been moved to src.core.logging_config
    """

    network: NetworkSettings = Field(default_factory=NetworkSettings)

    debug: bool = Field(default=False, description="Enable debug mode globally")

    class Config:
        """Settings configuration class."""

        env_prefix = "DATAFINANCE_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance
settings = Settings()
