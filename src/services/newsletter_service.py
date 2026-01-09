"""
Newsletter Service - Handles newsletter generation and formatting.

Business logic for:
- Generating AI summaries for articles
- Generating "Theme of the Week"
- Formatting newsletter HTML
- Saving newsletter files
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from sources.rss_fetcher import Article
from processors.summarizer import summarize_articles, generate_theme_of_week
from formatters.email_formatter import format_newsletter_html

logger = logging.getLogger(__name__)


class NewsletterService:
    """Service for generating and managing newsletters."""

    def __init__(self, config: Dict[str, Any], output_dir: Path):
        """
        Initialize newsletter service.

        Args:
            config: Configuration dictionary
            output_dir: Directory for saving newsletters
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"NewsletterService initialized with output_dir: {output_dir}")

    def enrich_articles_with_ai(self, articles: List[Article]) -> tuple[List[Article], Optional[Dict]]:
        """
        Enrich articles with AI summaries and generate theme.

        Args:
            articles: List of articles to enrich

        Returns:
            Tuple of (enriched articles, theme_of_week data)
        """
        if not articles:
            return [], None

        theme_of_week = None

        # Check for API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.info("GEMINI_API_KEY not set - skipping AI enrichment")
            return articles, theme_of_week

        try:
            logger.info(f"Starting AI enrichment for {len(articles)} articles")

            # Generate summaries (with parallel processing)
            articles = summarize_articles(articles, self.config, parallel=True)
            logger.info("AI summaries generated")

            # Generate theme of the week
            theme_of_week = generate_theme_of_week(articles, self.config)
            if theme_of_week and theme_of_week.get('enabled'):
                logger.info(f"Theme of the week: {theme_of_week.get('title', 'N/A')}")
            else:
                theme_of_week = None

            return articles, theme_of_week

        except Exception as e:
            logger.error(f"Error in AI enrichment: {e}")
            # Return articles without AI enrichment
            return articles, None

    def generate_newsletter_html(self, articles: List[Article],
                                theme_of_week: Optional[Dict] = None) -> str:
        """
        Generate HTML newsletter from articles.

        Args:
            articles: List of articles to include
            theme_of_week: Optional theme of the week data

        Returns:
            HTML newsletter content
        """
        try:
            logger.info(f"Generating newsletter HTML with {len(articles)} articles")

            html = format_newsletter_html(
                articles=articles,
                config=self.config,
                deep_dive=None,
                theme_of_week=theme_of_week
            )

            logger.info("Newsletter HTML generated successfully")
            return html

        except Exception as e:
            logger.error(f"Error generating newsletter HTML: {e}")
            raise

    def save_newsletter(self, html_content: str, date: Optional[str] = None) -> Path:
        """
        Save newsletter HTML to file.

        Args:
            html_content: HTML content to save
            date: Date string in YYYY-MM-DD format (default: today)

        Returns:
            Path to saved file
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        try:
            output_file = self.output_dir / f"newsletter_{date}.html"

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"Newsletter saved to {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Error saving newsletter: {e}")
            raise

    def get_newsletter_file(self, date: Optional[str] = None) -> Optional[Path]:
        """
        Get path to newsletter file for a date.

        Args:
            date: Date string in YYYY-MM-DD format (default: today)

        Returns:
            Path to file if exists, None otherwise
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        newsletter_file = self.output_dir / f"newsletter_{date}.html"

        if newsletter_file.exists():
            logger.debug(f"Found newsletter file: {newsletter_file}")
            return newsletter_file

        logger.debug(f"Newsletter file not found: {newsletter_file}")
        return None

    def read_newsletter_html(self, date: Optional[str] = None) -> Optional[str]:
        """
        Read newsletter HTML from file.

        Args:
            date: Date string in YYYY-MM-DD format (default: today)

        Returns:
            HTML content or None if file doesn't exist
        """
        newsletter_file = self.get_newsletter_file(date)
        if not newsletter_file:
            return None

        try:
            with open(newsletter_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading newsletter file: {e}")
            return None
