"""
Scout Agent - The Ingestion Engine for the AI This Week Newsletter.

This agent traverses the information landscape, collecting raw intelligence
from a curated SOURCE_MAP and outputting it to data/raw_intel.json.

Usage:
    python -m src.agents.scout
"""

import json
import logging
import feedparser
import requests
import concurrent.futures
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# SOURCE_MAP: The Whitelist of High-Fidelity Sources
# ============================================================================
# Each category maps to a list of sources with their URL and type (rss/scrape).

SOURCE_MAP = {
    'vertical_grain': [
        {
            'name': 'University of Saskatchewan - Agriculture',
            'url': 'https://usask.technologypublisher.com/rssDataFeed.aspx?category=agriculture+and+bioresources',
            'type': 'rss'
        },
        {
            'name': 'Protein Industries Canada',
            'url': 'https://www.proteinindustriescanada.ca/news-releases',
            'type': 'scrape'
        },
        {
            'name': 'Ground Truth Ag',
            'url': 'https://groundtruth.ag/',
            'type': 'scrape'
        },
    ],
    'deep_dive': [
        {
            'name': 'arXiv CS.AI',
            'url': 'http://arxiv.org/rss/cs.AI',
            'type': 'rss'
        },
    ],
    'headline': [
        {
            'name': 'Government of Canada - Innovation',
            'url': 'https://www.canada.ca/content/canadasite/api/nsc/rss/science-innovation.xml',
            'type': 'rss'
        },
        {
            'name': 'OECD AI Policy',
            'url': 'https://oecd.ai/en/feed',
            'type': 'rss'
        },
    ],
    'tools': [
        {
            'name': 'Google DeepMind Blog',
            'url': 'https://deepmind.google/discover/blog/rss.xml',
            'type': 'rss'
        },
    ],
    'bright_spot': [
        # Bright spots are often found within other feeds; this is a placeholder.
        # The Editor will filter for positive sentiment from all sources.
    ],
}


def fetch_rss_feed(url: str, source_name: str, category: str, max_age_days: int = 7) -> List[Dict[str, Any]]:
    """
    Fetch and parse an RSS feed.

    Args:
        url: The RSS feed URL.
        source_name: Human-readable name of the source.
        category: The category tag for these items (e.g., 'vertical_grain').
        max_age_days: Only include items published within this many days.

    Returns:
        List of article dictionaries.
    """
    articles = []
    cutoff_date = datetime.now() - timedelta(days=max_age_days)

    try:
        logger.info(f"Fetching RSS: {source_name} ({url})")
        feed = feedparser.parse(url)

        if feed.bozo:
            logger.warning(f"Feed parsing issue for {source_name}: {feed.bozo_exception}")

        for entry in feed.entries:
            # Parse publication date
            published = None
            if hasattr(entry, 'published'):
                try:
                    published = date_parser.parse(entry.published)
                except Exception:
                    published = datetime.now()
            elif hasattr(entry, 'updated'):
                try:
                    published = date_parser.parse(entry.updated)
                except Exception:
                    published = datetime.now()
            else:
                published = datetime.now()

            # Filter by age
            if published.replace(tzinfo=None) < cutoff_date:
                continue

            # Extract summary (handle arXiv abstracts)
            summary = ''
            if hasattr(entry, 'summary'):
                summary = entry.summary
            elif hasattr(entry, 'description'):
                summary = entry.description

            # Clean up title (remove newlines for arXiv)
            title = entry.get('title', 'Untitled')
            title = ' '.join(title.split())

            articles.append({
                'title': title,
                'link': entry.get('link', ''),
                'summary': summary[:500] if summary else '',  # Truncate long summaries
                'published': published.isoformat(),
                'source': source_name,
                'category': category,
            })

        logger.info(f"  -> Found {len(articles)} recent items from {source_name}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching {source_name}: {e}")
    except Exception as e:
        logger.error(f"Error fetching {source_name}: {e}")

    return articles


def scrape_protein_industries_canada() -> List[Dict[str, Any]]:
    """
    Scrape news releases from Protein Industries Canada.
    """
    articles = []
    url = 'https://www.proteinindustriescanada.ca/news-releases'

    try:
        logger.info(f"Scraping: Protein Industries Canada ({url})")
        response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find news items (adjust selectors based on actual site structure)
        news_items = soup.select('article.news-item, div.news-release, a.news-link')[:5]

        for item in news_items:
            title_elem = item.select_one('h2, h3, .title')
            link_elem = item if item.name == 'a' else item.select_one('a')

            if title_elem and link_elem:
                articles.append({
                    'title': title_elem.get_text(strip=True),
                    'link': link_elem.get('href', ''),
                    'summary': '',
                    'published': datetime.now().isoformat(),
                    'source': 'Protein Industries Canada',
                    'category': 'vertical_grain',
                })

        logger.info(f"  -> Found {len(articles)} items from Protein Industries Canada")

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error scraping Protein Industries Canada: {e}")
    except Exception as e:
        logger.error(f"Error scraping Protein Industries Canada: {e}")

    return articles


def scrape_ground_truth_ag() -> List[Dict[str, Any]]:
    """
    Scrape the latest news from Ground Truth Ag.
    """
    articles = []
    url = 'https://groundtruth.ag/'

    try:
        logger.info(f"Scraping: Ground Truth Ag ({url})")
        response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for news or blog sections (adjust selectors)
        news_items = soup.select('article, .news-item, .blog-post, section.content a')[:3]

        for item in news_items:
            title_elem = item.select_one('h1, h2, h3, .title')
            link_elem = item if item.name == 'a' else item.select_one('a')

            if title_elem:
                link = ''
                if link_elem:
                    link = link_elem.get('href', '')
                    if link and not link.startswith('http'):
                        link = f"https://groundtruth.ag{link}"

                articles.append({
                    'title': title_elem.get_text(strip=True),
                    'link': link,
                    'summary': '',
                    'published': datetime.now().isoformat(),
                    'source': 'Ground Truth Ag',
                    'category': 'vertical_grain',
                })

        logger.info(f"  -> Found {len(articles)} items from Ground Truth Ag")

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error scraping Ground Truth Ag: {e}")
    except Exception as e:
        logger.error(f"Error scraping Ground Truth Ag: {e}")

    return articles


def _process_source(source: Dict[str, Any], category: str) -> List[Dict[str, Any]]:
    """
    Helper function to process a single source.
    """
    articles = []
    try:
        if source['type'] == 'rss':
            articles = fetch_rss_feed(
                url=source['url'],
                source_name=source['name'],
                category=category
            )
        elif source['type'] == 'scrape':
            # Handle specific scrapers
            if 'proteinindustriescanada' in source['url']:
                articles = scrape_protein_industries_canada()
            elif 'groundtruth' in source['url']:
                articles = scrape_ground_truth_ag()
            else:
                logger.warning(f"No scraper implemented for: {source['name']}")
    except Exception as e:
        logger.error(f"Error processing source {source.get('name', 'unknown')}: {e}")

    return articles


def run_scout() -> Dict[str, Any]:
    """
    Execute the Scout agent: fetch all sources and aggregate results.

    Returns:
        Dictionary with raw intelligence data.
    """
    all_articles = []
    category_counts = {}

    logger.info("=" * 60)
    logger.info("🔍 SCOUT AGENT: Starting Intelligence Gathering")
    logger.info("=" * 60)

    # Process each category in SOURCE_MAP
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_category = {}

        for category, sources in SOURCE_MAP.items():
            category_counts[category] = 0
            for source in sources:
                future = executor.submit(_process_source, source, category)
                future_to_category[future] = category

        for future in concurrent.futures.as_completed(future_to_category):
            category = future_to_category[future]
            try:
                articles = future.result()
                if articles:
                    all_articles.extend(articles)
                    category_counts[category] += len(articles)
            except Exception as e:
                logger.error(f"An error occurred during source processing: {e}")

    # Build the report
    report = {
        'generated_at': datetime.now().isoformat(),
        'total_items': len(all_articles),
        'category_counts': category_counts,
        'articles': all_articles,
    }

    logger.info("=" * 60)
    logger.info("📊 SCOUT REPORT:")
    for cat, count in category_counts.items():
        logger.info(f"   {cat}: {count} items")
    logger.info(f"   TOTAL: {len(all_articles)} items")
    logger.info("=" * 60)

    return report


def save_raw_intel(report: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save the raw intelligence report to JSON.
    """
    if output_path is None:
        output_path = Path(__file__).parent.parent.parent / 'data' / 'raw_intel.json'

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"💾 Raw intelligence saved to: {output_path}")
    return output_path


def main():
    """Main entry point for the Scout agent."""
    report = run_scout()
    save_raw_intel(report)


if __name__ == '__main__':
    main()
