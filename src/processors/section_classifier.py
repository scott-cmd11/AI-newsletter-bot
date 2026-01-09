#!/usr/bin/env python3
"""
Section Classifier Module

Automatically classifies articles into newsletter sections:
- Headlines: Top scored, mixed governance/capabilities
- Bright Spot: Positive sentiment breakthroughs and innovations
- Tool: New tools, platforms, products
- Deep Dive: Research papers, policy reports, long-form analysis
- Grain Quality: Agriculture/farming AI applications
"""

import logging
import json
from typing import Optional
import os
import sys
from pathlib import Path

# Import Article model
sys.path.append(str(Path(__file__).parent.parent))
from sources.rss_fetcher import Article

logger = logging.getLogger(__name__)

# Try to import Gemini for sentiment detection
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Sentiment detection unavailable.")


# Keyword definitions for section classification
BRIGHT_SPOT_KEYWORDS = [
    'breakthrough',
    'cure',
    'innovation',
    'success',
    'achievement',
    'milestone',
    'wins',
    'discovery',
    'medical advance',
    'health benefit',
    'positive development',
    'good news',
    'solution',
    'beat',
    'exceeds',
    'record'
]

TOOL_KEYWORDS = [
    'tool',
    'platform',
    'app',
    'application',
    'launch',
    'release',
    'product',
    'library',
    'framework',
    'announces',
    'introduces',
    'debuts',
    'new service',
    'available now',
    'download',
    'open source'
]

RESEARCH_SOURCE_KEYWORDS = [
    'arxiv',
    'research',
    'journal',
    'paper',
    'study',
    'university',
    'academic',
    'institute',
    'white paper',
    'report',
    'policy report',
    'findings'
]

GRAIN_QUALITY_KEYWORDS = [
    'agriculture',
    'farming',
    'grain',
    'crop',
    'harvest',
    'agricultural',
    'farm',
    'wheat',
    'corn',
    'rice',
    'quality control',
    'soil',
    'farmer'
]


def detect_sentiment(article: Article, gemini_config: dict) -> str:
    """
    Use Gemini to classify article sentiment.

    Returns: "positive", "negative", "neutral", or "mixed"
    """
    if not GEMINI_AVAILABLE:
        logger.debug(f"Sentiment detection disabled (Gemini not available)")
        return "neutral"

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.debug("GEMINI_API_KEY not set, skipping sentiment detection")
        return "neutral"

    try:
        # Configure Gemini if not already done
        genai.configure(api_key=api_key)

        model_name = gemini_config.get('model', 'gemini-1.5-flash')

        prompt = f"""Classify the sentiment of this article as one of: positive, negative, neutral, or mixed.

DEFINITIONS:
- positive: Breakthroughs, innovations, solutions, good news, success stories, medical advances
- negative: Concerns, risks, problems, controversies, failures, security issues
- neutral: Factual reporting without clear positive or negative tone
- mixed: Contains both positive and negative elements

Article Title: {article.title}
Article Summary: {article.summary[:500]}

Respond with ONLY a JSON object (no markdown, no explanation):
{{"sentiment": "positive|negative|neutral|mixed"}}"""

        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)

        response_text = response.text.strip()

        # Handle markdown code blocks
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]

        result = json.loads(response_text)
        sentiment = result.get('sentiment', 'neutral').lower()

        # Validate sentiment value
        if sentiment not in ['positive', 'negative', 'neutral', 'mixed']:
            logger.warning(f"Invalid sentiment '{sentiment}', using 'neutral'")
            sentiment = 'neutral'

        logger.debug(f"Sentiment for '{article.title[:50]}': {sentiment}")
        return sentiment

    except json.JSONDecodeError as e:
        logger.warning(f"JSON parsing failed in sentiment detection: {e}")
        return "neutral"
    except Exception as e:
        logger.warning(f"Sentiment detection error: {e}")
        return "neutral"


def has_positive_sentiment_keywords(title: str, summary: str) -> bool:
    """Check if article has positive sentiment keywords."""
    text = (title + " " + summary).lower()
    return any(keyword in text for keyword in BRIGHT_SPOT_KEYWORDS)


def has_tool_keywords(title: str, summary: str) -> bool:
    """Check if article mentions tools/products/releases."""
    text = (title + " " + summary).lower()
    return any(keyword in text for keyword in TOOL_KEYWORDS)


def is_research_paper(article: Article) -> bool:
    """Detect if article is a research paper or academic publication."""
    text = (article.title + " " + article.source + " " + article.summary).lower()

    # Check for arxiv or research-heavy sources
    if 'arxiv' in text:
        return True

    # Check source names
    if any(keyword in text for keyword in ['arxiv', 'research paper', 'journal', 'university', 'academic']):
        return True

    # Check for academic keywords in title
    academic_indicators = ['research', 'study', 'analysis', 'findings', 'model', 'framework', 'algorithm']
    keyword_count = sum(1 for keyword in academic_indicators if keyword in article.title.lower())

    return keyword_count >= 2


def is_long_form(article: Article) -> bool:
    """Check if article appears to be long-form/deep analysis."""
    # Long-form indicators
    word_count = len(article.summary.split())

    # If summary is very long (>400 words), likely deep content
    if word_count > 400:
        return True

    # Check for report/whitepaper keywords
    text = (article.title + " " + article.source).lower()
    if any(keyword in text for keyword in ['white paper', 'report', 'analysis', 'deep dive']):
        return True

    return False


def has_grain_keywords(article: Article) -> bool:
    """Check if article is about agriculture/grain/farming AI."""
    text = (article.title + " " + article.summary).lower()
    return any(keyword in text for keyword in GRAIN_QUALITY_KEYWORDS)


def classify_article_section(
    article: Article,
    config: dict,
    use_sentiment_api: bool = True
) -> str:
    """
    Classify an article into a newsletter section.

    Args:
        article: Article to classify
        config: Configuration dict with gemini config
        use_sentiment_api: Whether to use Gemini API for sentiment (slower but more accurate)

    Returns:
        Section name: "headline", "bright_spot", "tool", "deep_dive", "grain_quality"
    """

    # Special case: Grain quality (can co-exist with other sections)
    if has_grain_keywords(article):
        logger.debug(f"Article '{article.title[:40]}' classified as grain_quality")
        # Note: In practice, we'll return grain_quality but also classify for other sections
        # For now, we prioritize this as a primary section
        return "grain_quality"

    # Tool detection (high priority)
    if article.category == 'tools' or has_tool_keywords(article.title, article.summary):
        logger.debug(f"Article '{article.title[:40]}' classified as tool")
        return "tool"

    # Deep dive detection (research papers or long-form analysis)
    if is_research_paper(article) or is_long_form(article):
        logger.debug(f"Article '{article.title[:40]}' classified as deep_dive")
        return "deep_dive"

    # Bright spot detection (positive sentiment)
    # Try keyword matching first (fast)
    has_positive_keywords = has_positive_sentiment_keywords(article.title, article.summary)

    # If positive keywords found or Gemini available, classify as bright spot
    sentiment = None
    if use_sentiment_api and GEMINI_AVAILABLE:
        gemini_config = config.get('gemini', {})
        sentiment = detect_sentiment(article, gemini_config)
        is_positive = sentiment == 'positive'
    else:
        is_positive = has_positive_keywords

    if is_positive:
        if sentiment:
            logger.debug(f"Article '{article.title[:40]}' classified as bright_spot (sentiment: {sentiment})")
        else:
            logger.debug(f"Article '{article.title[:40]}' classified as bright_spot (keywords)")
        return "bright_spot"

    # Default to headline
    logger.debug(f"Article '{article.title[:40]}' classified as headline")
    return "headline"


def classify_all_articles(
    articles: list,
    config: dict,
    use_sentiment_api: bool = True
) -> dict:
    """
    Classify all articles and return organized by section.

    Args:
        articles: List of Article objects
        config: Configuration dict
        use_sentiment_api: Whether to use Gemini for sentiment

    Returns:
        Dict with section names as keys and article lists as values
    """
    classified = {
        'headline': [],
        'bright_spot': [],
        'tool': [],
        'deep_dive': [],
        'grain_quality': []
    }

    for article in articles:
        section = classify_article_section(article, config, use_sentiment_api)
        article.section = section

        # Detect sentiment for all articles (useful for balance checking)
        if use_sentiment_api and GEMINI_AVAILABLE and not hasattr(article, 'sentiment'):
            gemini_config = config.get('gemini', {})
            article.sentiment = detect_sentiment(article, gemini_config)
        elif not hasattr(article, 'sentiment'):
            article.sentiment = 'neutral'

        classified[section].append(article)

    # Log distribution
    logger.info(f"Article classification distribution:")
    for section, articles_list in classified.items():
        logger.info(f"  {section}: {len(articles_list)}")

    return classified
