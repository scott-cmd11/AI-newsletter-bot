#!/usr/bin/env python3
"""
RSS Feed Fetcher Module

Fetches articles from Google Alerts and other RSS feeds.
"""

import feedparser
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional
import re


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
            "ai_commentary": self.ai_commentary
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
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    
    for alert in alerts_config:
        url = alert.get('url', '')
        if not url:
            print(f"  ⚠️  Skipping '{alert.get('name', 'Unknown')}' - no URL configured")
            continue
            
        print(f"  📡 Fetching: {alert.get('name', url[:50])}")
        
        try:
            feed = feedparser.parse(url)
            
            if feed.bozo and not feed.entries:
                print(f"    ⚠️  Error parsing feed: {feed.bozo_exception}")
                continue
                
            for entry in feed.entries:
                pub_date = parse_date(entry)
                
                # Skip old articles
                if pub_date and pub_date < cutoff_date:
                    continue
                    
                article = Article(
                    title=clean_html(entry.get('title', 'No title')),
                    url=entry.get('link', ''),
                    source=alert.get('name', 'Google Alerts'),
                    published=pub_date,
                    summary=clean_html(entry.get('summary', '')),
                    priority=alert.get('priority', 'medium')
                )
                articles.append(article)
                
            print(f"    ✓ Found {len(feed.entries)} entries")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            
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
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    
    for feed_config in feeds_config:
        url = feed_config.get('url', '')
        if not url:
            continue
            
        print(f"  📡 Fetching: {feed_config.get('name', url[:50])}")
        
        try:
            feed = feedparser.parse(url)
            
            if feed.bozo and not feed.entries:
                print(f"    ⚠️  Warning: {feed.bozo_exception}")
                continue
                
            count = 0
            for entry in feed.entries:
                pub_date = parse_date(entry)
                
                if pub_date and pub_date < cutoff_date:
                    continue
                    
                article = Article(
                    title=clean_html(entry.get('title', 'No title')),
                    url=entry.get('link', ''),
                    source=feed_config.get('name', 'RSS Feed'),
                    published=pub_date,
                    summary=clean_html(entry.get('summary', entry.get('description', ''))),
                    category=feed_config.get('category', ''),
                    priority=feed_config.get('priority', 'medium')
                )
                articles.append(article)
                count += 1
                
            print(f"    ✓ Found {count} recent articles")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            
    return articles


def fetch_all_articles(config: dict) -> List[Article]:
    """
    Fetch articles from all configured sources.
    
    Args:
        config: Full configuration dictionary
        
    Returns:
        Combined list of all articles
    """
    all_articles = []
    max_age = config.get('max_age_days', 7)
    
    # Fetch from Google Alerts
    google_alerts = config.get('google_alerts', [])
    if google_alerts:
        print("\n📬 Fetching Google Alerts...")
        alerts_articles = fetch_google_alerts(google_alerts, max_age)
        all_articles.extend(alerts_articles)
        print(f"  Total from Google Alerts: {len(alerts_articles)}")
    
    # Fetch from RSS feeds
    rss_feeds = config.get('rss_feeds', [])
    if rss_feeds:
        print("\n📰 Fetching RSS Feeds...")
        rss_articles = fetch_rss_feeds(rss_feeds, max_age)
        all_articles.extend(rss_articles)
        print(f"  Total from RSS Feeds: {len(rss_articles)}")
    
    # Deduplicate by URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article.url not in seen_urls:
            seen_urls.add(article.url)
            unique_articles.append(article)
            
    print(f"\n📊 Total unique articles: {len(unique_articles)}")
    
    return unique_articles
