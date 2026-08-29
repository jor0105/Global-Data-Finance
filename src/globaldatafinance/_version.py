"""Resolve the installed package version without importing application code."""

from importlib import metadata

try:
    __version__ = metadata.version('globaldatafinance')
except metadata.PackageNotFoundError:
    __version__ = '0.2.0'

__all__ = ['__version__']
