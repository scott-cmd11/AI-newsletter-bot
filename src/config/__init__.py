"""Configuration management module."""

from .loader import load_config, ConfigError

__all__ = ['load_config', 'ConfigError']
