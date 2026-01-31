#!/usr/bin/env python3
"""
Article Scoring Module

Scores and ranks articles based on relevance, recency, and topic matching.
"""

from typing import List, Union, Dict, Any, Optional
from datetime import datetime
import re
import logging

# Import from parent
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from sources.rss_fetcher import Article

logger = logging.getLogger(__name__)


def _normalize_topics_config(topics_config: Union[Dict, List]) -> List[Dict[str, Any]]:
    """
    Normalize topics configuration to a list of dicts with pre-lowercased keywords.
    Handles both legacy dictionary format and new list format.
    """
    normalized = []

    try:
        if isinstance(topics_config, dict):
            for category, config in topics_config.items():
                if not config:
                    continue
                normalized.append({
                    'category': category,
                    'keywords': [k.lower() for k in config.get('keywords', []) if k],
                    'boost': float(config.get('priority_boost', 1.0))
                })
        elif isinstance(topics_config, list):
            for item in topics_config:
                if not item:
                    continue
                # Extract category from 'category' field or 'name' if missing
                category = item.get('category', item.get('name', 'unknown'))
                keywords = item.get('keywords', [])
                boost = float(item.get('priority', item.get('priority_boost', 1.0)))

                normalized.append({
                    'category': category,
                    'keywords': [k.lower() for k in keywords if k],
                    'boost': boost
                })
    except Exception as e:
        logger.error(f"Error normalizing topics config: {e}")

    return normalized


def _calculate_topic_score_fast(text_lower: str, normalized_topics: List[Dict[str, Any]]) -> tuple[float, str]:
    """
    Fast version of topic scoring using pre-computed text and normalized config.
    """
    best_score = 0.0
    best_category = ""

    for topic in normalized_topics:
        keywords = topic['keywords']
        if not keywords:
            continue

        # Count keyword matches
        # Optimization: use optimized search if needed, but linear scan over keywords is usually fine
        # if keywords are not too many.
        # Since we pre-lowercased keywords and text, we just check existence.

        matches = sum(1 for kw in keywords if kw in text_lower)

        if matches > 0:
            category_score = matches * topic['boost']
            if category_score > best_score:
                best_score = category_score
                best_category = topic['category']

    return best_score, best_category


def calculate_topic_score(article: Article, topics_config: Union[Dict, List]) -> tuple[float, str]:
    """
    Calculate topic relevance score and classify article.

    Legacy wrapper that normalizes config on the fly.
    """
    try:
        # Validate inputs
        if not article:
            logger.warning("calculate_topic_score called with None article")
            return 0.0, ""

        if not topics_config:
            return 0.0, ""

        # Build text
        title = article.title or ""
        summary = article.summary or ""
        text_lower = f"{title} {summary}".lower()

        # Normalize config (this is the slow path, used if called individually)
        normalized_topics = _normalize_topics_config(topics_config)

        return _calculate_topic_score_fast(text_lower, normalized_topics)

    except Exception as e:
        logger.error(f"Error in calculate_topic_score: {e}")
        return 0.0, ""


def calculate_canadian_score(article: Article, canadian_keywords: List[str], boost: float, text_lower: str = None) -> float:
    """
    Calculate Canadian content relevance boost.
    """
    if text_lower is None:
        text_lower = f"{article.title} {article.summary}".lower()

    # Assume canadian_keywords might not be lowercased if coming from legacy path,
    # but for optimization we should assume they are if passed from score_articles.
    # To be safe, we'll just check.
    
    matches = sum(1 for kw in canadian_keywords if kw.lower() in text_lower)
    
    if matches > 0:
        return boost * min(matches, 3)  # Cap at 3x multiplier
    return 1.0


def calculate_recency_score(article: Article) -> float:
    """
    Calculate recency score - newer articles score higher.
    """
    if not article.published:
        return 0.5
        
    days_old = (datetime.now() - article.published).days
    
    if days_old <= 1:
        return 1.0
    elif days_old <= 3:
        return 0.8
    elif days_old <= 5:
        return 0.6
    elif days_old <= 7:
        return 0.4
    else:
        return 0.2


def calculate_priority_score(article: Article) -> float:
    """
    Calculate base priority score from source configuration.
    """
    priority_map = {
        'high': 1.5,
        'medium': 1.0,
        'low': 0.5
    }
    return priority_map.get(article.priority, 1.0)


def should_exclude(article: Article, exclude_patterns: List[str], text_lower: str = None) -> bool:
    """
    Check if article should be excluded based on patterns.
    """
    if text_lower is None:
        text_lower = f"{article.title} {article.summary}".lower()
    
    for pattern in exclude_patterns:
        if pattern.lower() in text_lower:
            return True
    return False


def score_articles(articles: List[Article], config: dict) -> List[Article]:
    """
    Score and rank all articles.
    
    Args:
        articles: List of Article objects to score
        config: Configuration dictionary
        
    Returns:
        List of scored and sorted articles (highest score first)
    """
    # 1. Pre-process configuration (Optimization)
    raw_topics = config.get('topics', {})
    normalized_topics = _normalize_topics_config(raw_topics)

    canadian_keywords = config.get('canadian_keywords', [])
    # Pre-lowercase for consistency, though helper handles mixed case
    canadian_keywords_lower = [k.lower() for k in canadian_keywords]

    canadian_boost = config.get('canadian_boost', 1.5)

    exclude_patterns = config.get('exclude_patterns', [])
    exclude_patterns_lower = [p.lower() for p in exclude_patterns]
    
    scored_articles = []
    
    for article in articles:
        # Optimization: Compute text once per article
        title = article.title or ""
        summary = article.summary or ""
        text_lower = f"{title} {summary}".lower()

        # Check exclusions
        # Note: should_exclude expects patterns, but we pass lowercased patterns.
        # The helper calls .lower() on pattern.
        # We can optimize should_exclude to accept pre-lowercased patterns too,
        # but for now let's use the helper with text_lower.
        # Ideally, we modify should_exclude to take pre-lowercased patterns.
        # But let's stick to just passing text_lower for safety.
        if should_exclude(article, exclude_patterns, text_lower=text_lower):
            continue
            
        # Calculate component scores
        topic_score, category = _calculate_topic_score_fast(text_lower, normalized_topics)

        # We pass original keywords to calculate_canadian_score because it calls .lower() on them.
        # But we pass text_lower.
        canadian_multiplier = calculate_canadian_score(article, canadian_keywords, canadian_boost, text_lower=text_lower)

        recency_score = calculate_recency_score(article)
        priority_score = calculate_priority_score(article)
        
        # Assign category
        article.category = category if category else article.category
        
        # Calculate final score
        # Base score from topic relevance
        base_score = max(topic_score, 1.0)  # Minimum 1.0
        
        # Apply multipliers
        final_score = base_score * canadian_multiplier * recency_score * priority_score
        
        article.score = round(final_score, 2)
        scored_articles.append(article)
        
    # Sort by score (highest first)
    scored_articles.sort(key=lambda a: a.score, reverse=True)
    
    return scored_articles


def get_top_articles(articles: List[Article], max_articles: int = 8) -> List[Article]:
    """
    Get the top N articles by score.
    """
    return articles[:max_articles]


def print_article_rankings(articles: List[Article], top_n: int = 10):
    """
    Print article rankings for review.
    """
    print(f"\n🏆 Top {min(top_n, len(articles))} Articles by Score:\n")
    print("-" * 80)
    
    for i, article in enumerate(articles[:top_n], 1):
        text_lower = f"{article.title} {article.summary}".lower()
        canadian = "🍁" if any(kw in text_lower
                               for kw in ['canada', 'canadian', 'toronto', 'montreal']) else "  "
        
        print(f"{i:2}. [{article.score:5.2f}] {canadian} {article.title[:60]}")
        print(f"     📂 {article.category or 'uncategorized'} | 📰 {article.source}")
        print(f"     🔗 {article.url[:70]}")
        print()
