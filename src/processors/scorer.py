#!/usr/bin/env python3
"""
Article Scoring Module

Scores and ranks articles based on relevance, recency, and topic matching.
"""

from typing import List
from datetime import datetime
import re
import logging

# Import from parent
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from sources.rss_fetcher import Article

logger = logging.getLogger(__name__)


def calculate_topic_score(article: Article, topics_config: any) -> tuple[float, str]:
    """
    Calculate topic relevance score and classify article.

    Args:
        article: Article to score
        topics_config: Topics configuration (list of dicts or legacy dict)

    Returns:
        Tuple of (score_boost, matched_category)
    """
    try:
        # Validate inputs
        if not article:
            logger.warning("calculate_topic_score called with None article")
            return 0.0, ""

        if not topics_config:
            return 0.0, ""

        # Normalize topics to list
        topics_list = []
        if isinstance(topics_config, list):
            topics_list = topics_config
        elif isinstance(topics_config, dict):
            # Legacy format support
            for name, data in topics_config.items():
                if isinstance(data, dict):
                    item = data.copy()
                    item.setdefault('name', name)
                    item.setdefault('category', name)
                    # Legacy priority_boost maps to priority
                    item.setdefault('priority', item.get('priority_boost', 1.0))
                    topics_list.append(item)

        if not topics_list:
            return 0.0, ""

        # Build text for matching (handle None values)
        title = article.title or ""
        summary = article.summary or ""
        text = f"{title} {summary}".lower()

        best_score = 0.0
        best_category = ""

        for topic in topics_list:
            if not topic:
                continue

            keywords = topic.get('keywords', [])
            if not keywords:
                continue

            boost = topic.get('priority', topic.get('priority_boost', 1.0))

            # Validate boost
            try:
                boost = float(boost)
            except (ValueError, TypeError):
                logger.warning(f"Invalid boost value {boost}, using 1.0")
                boost = 1.0

            # Count keyword matches
            matches = sum(1 for kw in keywords if kw and kw.lower() in text)

            if matches > 0:
                category_score = matches * boost
                if category_score > best_score:
                    best_score = category_score
                    best_category = topic.get('category', topic.get('name', ''))

        return best_score, best_category

    except Exception as e:
        logger.error(f"Error in calculate_topic_score: {e}")
        return 0.0, ""


def calculate_canadian_score(article: Article, canadian_keywords: List[str], boost: float) -> float:
    """
    Calculate Canadian content relevance boost.
    """
    text = f"{article.title} {article.summary}".lower()
    
    matches = sum(1 for kw in canadian_keywords if kw.lower() in text)
    
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


def should_exclude(article: Article, exclude_patterns: List[str]) -> bool:
    """
    Check if article should be excluded based on patterns.
    """
    text = f"{article.title} {article.summary}".lower()
    
    for pattern in exclude_patterns:
        if pattern.lower() in text:
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
    topics_config = config.get('topics', {})
    canadian_keywords = config.get('canadian_keywords', [])
    canadian_boost = config.get('canadian_boost', 1.5)
    exclude_patterns = config.get('exclude_patterns', [])
    
    scored_articles = []
    
    for article in articles:
        # Check exclusions
        if should_exclude(article, exclude_patterns):
            continue
            
        # Calculate component scores
        topic_score, category = calculate_topic_score(article, topics_config)
        canadian_multiplier = calculate_canadian_score(article, canadian_keywords, canadian_boost)
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
        canadian = "🍁" if any(kw.lower() in f"{article.title} {article.summary}".lower() 
                               for kw in ['canada', 'canadian', 'toronto', 'montreal']) else "  "
        
        print(f"{i:2}. [{article.score:5.2f}] {canadian} {article.title[:60]}")
        print(f"     📂 {article.category or 'uncategorized'} | 📰 {article.source}")
        print(f"     🔗 {article.url[:70]}")
        print()
