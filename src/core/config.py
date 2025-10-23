"""Centralized configuration module for global DataFinance settings.

This module provides type-safe, validated configuration management
with support for environment variables and default values.

ONLY contains truly global configurations that apply across all data sources
(CVM, B3, SEC, etc.). Source-specific configs remain in their respective domains.

Example:
    >>> from src.core.config import settings
    >>> print(settings.logging.level)
    INFO
    >>> # Override via environment variable
    >>> # export DATAFIN_LOG_LEVEL=DEBUG
"""

import logging
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class LoggingSettings(BaseSettings):
    """Global logging configuration for the entire library."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Global logging level"
    )

    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format",
    )

    log_file: Optional[str] = Field(
        default=None, description="Path to log file (None = console only)"
    )

    structured: bool = Field(
        default=False, description="Enable structured logging (JSON format)"
    )

    class Config:
        env_prefix = "DATAFIN_LOG_"
        case_sensitive = False

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate log level."""
        return v.upper()


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
        default="DataFinance/1.0 (Python Financial Data Library)",
        description="User agent for HTTP requests",
    )

    class Config:
        env_prefix = "DATAFIN_NETWORK_"
        case_sensitive = False


class Settings(BaseSettings):
    """Main settings container for global configurations.

    Contains only truly global settings. Source-specific configurations
    (CVM, B3, SEC) remain in their respective domain modules.
    """

    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    network: NetworkSettings = Field(default_factory=NetworkSettings)

    debug: bool = Field(default=False, description="Enable debug mode globally")

    class Config:
        env_prefix = "DATAFIN_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"

    def configure_logging(self) -> None:
        """Configure Python logging based on settings."""
        import sys

        handlers = [logging.StreamHandler(sys.stdout)]

        if self.logging.log_file:
            handlers.append(logging.FileHandler(self.logging.log_file))

        logging.basicConfig(
            level=getattr(logging, self.logging.level),
            format=self.logging.format,
            handlers=handlers,
            force=True,
        )

        if self.debug:
            logging.getLogger("src").setLevel(logging.DEBUG)


# Singleton instance
settings = Settings()

# Auto-configure logging on import
settings.configure_logging()
