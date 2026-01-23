#!/usr/bin/env python3
"""
RSS Feed Fetcher Module

Fetches articles from Google Alerts and other RSS feeds.
"""

import feedparser
import logging
import concurrent.futures
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import cache module
try:
    from cache import get_cached_articles, cache_articles
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.debug("Cache module not available")


@dataclass
class Article:
    """Represents a fetched article."""
    title: str
    url: str
    source: str
    published: datetime
    summary: str
    category: str = ""
    priority: str = "medium"
    score: float = 0.0
    ai_summary: str = ""
    ai_commentary: str = ""

    # New fields for section-based newsletter
    section: str = ""  # headline, bright_spot, tool, deep_dive, grain_quality
    sentiment: str = ""  # positive, negative, neutral, mixed
    canadian_context: str = ""  # Generated Canadian angle

    def __post_init__(self):
        """Validate article data."""
        # Ensure title is not empty
        if not self.title or not self.title.strip():
            logger.warning(f"Article has empty title, using placeholder")
            self.title = "[No title]"

        # Ensure URL is not empty
        if not self.url or not self.url.strip():
            logger.warning(f"Article '{self.title}' has empty URL")
            self.url = ""

        # Ensure source is not empty
        if not self.source or not self.source.strip():
            self.source = "Unknown"

        # Validate priority
        if self.priority not in ['low', 'medium', 'high']:
            logger.warning(f"Invalid priority '{self.priority}', using 'medium'")
            self.priority = "medium"

        # Ensure summary is a string
        if not isinstance(self.summary, str):
            self.summary = str(self.summary) if self.summary else ""

        # Ensure published is a datetime
        if not isinstance(self.published, datetime):
            logger.warning(f"Invalid published date, using current time")
            self.published = datetime.now()

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "published": self.published.isoformat() if self.published else None,
            "summary": self.summary,
            "category": self.category,
            "priority": self.priority,
            "score": self.score,
            "ai_summary": self.ai_summary,
            "ai_commentary": self.ai_commentary,
            "section": self.section,
            "sentiment": self.sentiment,
            "canadian_context": self.canadian_context
        }


def parse_date(entry) -> Optional[datetime]:
    """Parse publication date from feed entry."""
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])
    if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6])
    return datetime.now()


def clean_html(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()


def _process_feed_item(feed_config: dict, max_age_days: int, default_source: str) -> List[Article]:
    """
    Helper to process a single feed config.
    
    Args:
        feed_config: Dictionary containing feed configuration
        max_age_days: Maximum age of articles to include
        default_source: Default source name if not provided in config
        
    Returns:
        List of Article objects
    """
    articles = []
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    
    url = feed_config.get('url', '')
    if not url:
        logger.warning(f"Skipping '{feed_config.get('name', 'Unknown')}' - no URL configured")
        print(f"  ⚠️  Skipping '{feed_config.get('name', 'Unknown')}' - no URL configured")
        return []

    feed_name = feed_config.get('name', url[:50])
    print(f"  📡 Fetching: {feed_name}")
    logger.debug(f"Fetching {default_source}: {feed_name}")

    try:
        feed = feedparser.parse(url)

        if feed.bozo and not feed.entries:
            logger.warning(f"Error parsing feed {feed_name}: {feed.bozo_exception}")
            print(f"    ⚠️  Error/Warning parsing feed {feed_name}: {feed.bozo_exception}")
            # Continue if there are entries, otherwise return
            if not feed.entries:
                return []

        count = 0
        for entry in feed.entries:
            pub_date = parse_date(entry)

            # Skip old articles
            if pub_date and pub_date < cutoff_date:
                continue

            article = Article(
                title=clean_html(entry.get('title', 'No title')),
                url=entry.get('link', ''),
                source=feed_config.get('name', default_source),
                published=pub_date,
                summary=clean_html(entry.get('summary', entry.get('description', ''))),
                category=feed_config.get('category', ''),
                priority=feed_config.get('priority', 'medium')
            )
            articles.append(article)
            count += 1

        print(f"    ✓ Found {count} recent articles in {feed_name}")
        logger.debug(f"Found {count} recent articles in {feed_name}")

    except Exception as e:
        logger.error(f"Error fetching {feed_name}: {e}")
        print(f"    ❌ Error fetching {feed_name}: {e}")

    return articles


def fetch_google_alerts(alerts_config: List[dict], max_age_days: int = 7) -> List[Article]:
    """
    Fetch articles from Google Alerts RSS feeds.

    Args:
        alerts_config: List of Google Alert configurations with 'url', 'name', 'priority'
        max_age_days: Maximum age of articles to include

    Returns:
        List of Article objects
    """
    articles = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Create a list of futures
        futures = [
            executor.submit(_process_feed_item, alert, max_age_days, "Google Alerts")
            for alert in alerts_config
        ]

        # Collect results as they complete
        for future in concurrent.futures.as_completed(futures):
            try:
                feed_articles = future.result()
                articles.extend(feed_articles)
            except Exception as e:
                logger.error(f"Thread execution failed: {e}")
            
    return articles


def fetch_rss_feeds(feeds_config: List[dict], max_age_days: int = 7) -> List[Article]:
    """
    Fetch articles from standard RSS feeds.
    
    Args:
        feeds_config: List of feed configurations
        max_age_days: Maximum age of articles to include
        
    Returns:
        List of Article objects
    """
    articles = []
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Create a list of futures
        futures = [
            executor.submit(_process_feed_item, feed_config, max_age_days, "RSS Feed")
            for feed_config in feeds_config
        ]

        # Collect results as they complete
        for future in concurrent.futures.as_completed(futures):
            try:
                feed_articles = future.result()
                articles.extend(feed_articles)
            except Exception as e:
                logger.error(f"Thread execution failed: {e}")
            
    return articles


def fetch_all_articles(config: dict, use_cache: bool = True) -> List[Article]:
    """
    Fetch articles from all configured sources.

    Args:
        config: Full configuration dictionary
        use_cache: Use cached articles if available (default True)

    Returns:
        Combined list of all articles
    """
    # Try to use cache first
    if use_cache and CACHE_AVAILABLE:
        cached = get_cached_articles("articles")
        if cached:
            print("\n✓ Using cached articles")
            logger.info(f"Using {len(cached)} cached articles")
            # Reconstruct Article objects from cached dicts
            articles_list = []
            for article_dict in cached:
                try:
                    pub_date = article_dict.get('published')
                    if pub_date and isinstance(pub_date, str):
                        pub_date = datetime.fromisoformat(pub_date)
                    article = Article(
                        title=article_dict.get('title', ''),
                        url=article_dict.get('url', ''),
                        source=article_dict.get('source', ''),
                        published=pub_date or datetime.now(),
                        summary=article_dict.get('summary', ''),
                        category=article_dict.get('category', ''),
                        priority=article_dict.get('priority', 'medium'),
                        score=article_dict.get('score', 0.0),
                        ai_summary=article_dict.get('ai_summary', ''),
                        ai_commentary=article_dict.get('ai_commentary', '')
                    )
                    articles_list.append(article)
                except Exception as e:
                    logger.warning(f"Error reconstructing cached article: {e}")
            if articles_list:
                return articles_list

    all_articles = []
    max_age = config.get('max_age_days', 7)

    # Fetch from Google Alerts
    google_alerts = config.get('google_alerts', [])
    if google_alerts:
        print("\n📬 Fetching Google Alerts...")
        logger.info(f"Fetching {len(google_alerts)} Google Alerts")
        alerts_articles = fetch_google_alerts(google_alerts, max_age)
        all_articles.extend(alerts_articles)
        print(f"  Total from Google Alerts: {len(alerts_articles)}")
        logger.info(f"Got {len(alerts_articles)} articles from Google Alerts")

    # Fetch from RSS feeds
    rss_feeds = config.get('rss_feeds', [])
    if rss_feeds:
        print("\n📰 Fetching RSS Feeds...")
        logger.info(f"Fetching {len(rss_feeds)} RSS feeds")
        rss_articles = fetch_rss_feeds(rss_feeds, max_age)
        all_articles.extend(rss_articles)
        print(f"  Total from RSS Feeds: {len(rss_articles)}")
        logger.info(f"Got {len(rss_articles)} articles from RSS feeds")

    # Deduplicate by URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article.url not in seen_urls:
            seen_urls.add(article.url)
            unique_articles.append(article)

    print(f"\n📊 Total unique articles: {len(unique_articles)}")
    logger.info(f"Total unique articles after deduplication: {len(unique_articles)}")

    # Cache the articles
    if CACHE_AVAILABLE:
        cache_articles(unique_articles, "articles")
        logger.debug(f"Cached {len(unique_articles)} articles")

    return unique_articles
