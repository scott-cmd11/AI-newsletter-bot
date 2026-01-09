"""Unit tests for configuration module."""

import unittest
import tempfile
from pathlib import Path
import yaml
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.loader import load_config, ConfigError, FullConfig


class TestConfigLoader(unittest.TestCase):
    """Test configuration loading and validation."""

    def test_valid_config(self):
        """Test loading a valid configuration."""
        config_dict = {
            'newsletter': {
                'name': 'Test Newsletter',
                'max_articles': 10
            },
            'google_alerts': [
                {
                    'name': 'AI News',
                    'url': 'https://example.com/feed',
                    'priority': 'high',
                    'category': 'capabilities'
                }
            ],
            'rss_feeds': [],
            'gemini': {
                'model': 'gemini-1.5-flash',
                'summary_style': 'analytical'
            }
        }

        # Create temp config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            self.assertIsNotNone(config)
            self.assertEqual(config['newsletter']['name'], 'Test Newsletter')
            self.assertEqual(len(config['google_alerts']), 1)
        finally:
            Path(temp_path).unlink()

    def test_invalid_priority(self):
        """Test that invalid priority values are rejected."""
        config_dict = {
            'newsletter': {'name': 'Test'},
            'google_alerts': [
                {
                    'name': 'AI News',
                    'url': 'https://example.com/feed',
                    'priority': 'invalid_priority',  # Should be 'low', 'medium', or 'high'
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name

        try:
            with self.assertRaises(ConfigError):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_missing_config_file(self):
        """Test that missing config file raises error."""
        with self.assertRaises(ConfigError):
            load_config('/nonexistent/path/config.yaml')

    def test_invalid_yaml(self):
        """Test that invalid YAML raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")  # Invalid YAML
            temp_path = f.name

        try:
            with self.assertRaises(ConfigError):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_empty_config(self):
        """Test that empty config file raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")  # Empty file
            temp_path = f.name

        try:
            with self.assertRaises(ConfigError):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_config_with_defaults(self):
        """Test that missing optional fields get default values."""
        config_dict = {
            'newsletter': {'name': 'Test'}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            # Should have default values
            self.assertEqual(config['gemini']['model'], 'gemini-1.5-flash')
            self.assertEqual(config['max_age_days'], 7)
        finally:
            Path(temp_path).unlink()

    def test_valid_summary_styles(self):
        """Test that valid summary styles are accepted."""
        for style in ['analytical', 'brief', 'detailed']:
            config_dict = {
                'newsletter': {'name': 'Test'},
                'gemini': {'summary_style': style}
            }

            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(config_dict, f)
                temp_path = f.name

            try:
                config = load_config(temp_path)
                self.assertEqual(config['gemini']['summary_style'], style)
            finally:
                Path(temp_path).unlink()

    def test_invalid_summary_style(self):
        """Test that invalid summary style is rejected."""
        config_dict = {
            'newsletter': {'name': 'Test'},
            'gemini': {'summary_style': 'invalid_style'}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name

        try:
            with self.assertRaises(ConfigError):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_max_age_validation(self):
        """Test that max_age_days must be positive."""
        config_dict = {
            'newsletter': {'name': 'Test'},
            'max_age_days': 0  # Invalid: must be >= 1
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name

        try:
            with self.assertRaises(ConfigError):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()


class TestConfigModel(unittest.TestCase):
    """Test Pydantic config models."""

    def test_newsletter_config_model(self):
        """Test NewsletterConfig model validation."""
        from config.loader import NewsletterConfig
        config = NewsletterConfig(name="Test", max_articles=8)
        self.assertEqual(config.name, "Test")
        self.assertEqual(config.max_articles, 8)

    def test_google_alert_config_priority(self):
        """Test GoogleAlertConfig priority validation."""
        from config.loader import GoogleAlertConfig
        # Valid priority
        alert = GoogleAlertConfig(name="Test", url="https://example.com", priority="high")
        self.assertEqual(alert.priority, "high")

        # Invalid priority should raise error
        with self.assertRaises(Exception):
            GoogleAlertConfig(name="Test", url="https://example.com", priority="invalid")


if __name__ == '__main__':
    unittest.main()
