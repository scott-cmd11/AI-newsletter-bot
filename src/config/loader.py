"""
Configuration management with Pydantic validation.

Centralizes config loading and validation across all modules.
"""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

import yaml
from pydantic import BaseModel, Field, validator, ValidationError


# Configuration Models using Pydantic
class NewsletterConfig(BaseModel):
    """Newsletter settings."""
    name: str = "AI This Week"
    tagline: str = "Key AI Developments You Should Know"
    target_day: str = "Thursday"
    send_day: str = "Friday"
    max_articles: int = 8

    class Config:
        extra = "ignore"  # Allow extra fields without error


class GoogleAlertConfig(BaseModel):
    """Google Alerts feed configuration."""
    name: str
    url: str
    priority: str = "medium"
    category: str = ""

    @validator('priority')
    def validate_priority(cls, v):
        if v not in ['low', 'medium', 'high']:
            raise ValueError(f"Priority must be 'low', 'medium', or 'high', got {v}")
        return v

    class Config:
        extra = "ignore"


class RSSFeedConfig(BaseModel):
    """RSS feed configuration."""
    name: str
    url: str
    priority: str = "medium"
    category: str = ""

    @validator('priority')
    def validate_priority(cls, v):
        if v not in ['low', 'medium', 'high']:
            raise ValueError(f"Priority must be 'low', 'medium', or 'high', got {v}")
        return v

    class Config:
        extra = "ignore"


class TopicConfig(BaseModel):
    """Topic/keyword configuration."""
    name: str
    keywords: List[str]
    category: str
    priority: Optional[float] = 1.0

    class Config:
        extra = "ignore"


class GeminiConfig(BaseModel):
    """Google Gemini AI configuration."""
    model: str = "gemini-1.5-flash"
    summary_style: str = "analytical"
    include_commentary: bool = True
    max_summary_length: int = 150

    @validator('summary_style')
    def validate_style(cls, v):
        if v not in ['analytical', 'brief', 'detailed']:
            raise ValueError(f"summary_style must be 'analytical', 'brief', or 'detailed', got {v}")
        return v

    class Config:
        extra = "ignore"


class ThemeConfig(BaseModel):
    """Theme of the week configuration."""
    enabled: bool = True
    length: int = 150

    class Config:
        extra = "ignore"


class FullConfig(BaseModel):
    """Complete configuration schema."""
    newsletter: NewsletterConfig
    google_alerts: List[GoogleAlertConfig] = Field(default_factory=list)
    rss_feeds: List[RSSFeedConfig] = Field(default_factory=list)
    topics: Optional[List[TopicConfig]] = Field(default_factory=list)
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    theme_of_week: ThemeConfig = Field(default_factory=ThemeConfig)
    max_age_days: int = 7
    canadian_boost: float = 1.5

    @validator('max_age_days')
    def validate_max_age(cls, v):
        if v < 1:
            raise ValueError("max_age_days must be at least 1")
        return v

    class Config:
        extra = "allow"  # Allow additional fields for extensibility


class ConfigError(Exception):
    """Configuration loading or validation error."""
    pass


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load and validate configuration from YAML file.

    Args:
        config_path: Path to sources.yaml. If None, uses default location.

    Returns:
        Validated configuration dictionary

    Raises:
        ConfigError: If config file not found or validation fails
    """
    if config_path is None:
        # Default path: config/sources.yaml relative to project root
        config_path = Path(__file__).parent.parent.parent / "config" / "sources.yaml"

    config_path = Path(config_path)

    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML: {e}")
    except Exception as e:
        raise ConfigError(f"Failed to load config file: {e}")

    if not raw_config:
        raise ConfigError("Config file is empty")

    # Fix topics format if it's a dict instead of list
    if isinstance(raw_config.get('topics'), dict):
        # Convert dict format to list format
        topics_list = []
        for topic_name, topic_data in raw_config.get('topics', {}).items():
            if isinstance(topic_data, dict):
                topics_list.append({
                    'name': topic_name,
                    'keywords': topic_data.get('keywords', []),
                    'category': topic_data.get('category', topic_name),
                    'priority': topic_data.get('priority_boost', 1.0)
                })
        raw_config['topics'] = topics_list

    # Validate with Pydantic
    try:
        validated = FullConfig(**raw_config)
        return validated.dict()
    except ValidationError as e:
        error_details = "\n".join([
            f"  - {err['loc'][0]}: {err['msg']}"
            for err in e.errors()
        ])
        raise ConfigError(f"Config validation failed:\n{error_details}")


def get_config() -> Dict[str, Any]:
    """
    Get the configuration (singleton-like behavior).

    Returns:
        Validated configuration dictionary

    Raises:
        ConfigError: If config cannot be loaded
    """
    return load_config()
