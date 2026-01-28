#!/usr/bin/env python3
"""
Article Scoring Module

Scores and ranks articles based on relevance, recency, and topic matching.
"""

from typing import List, Union, Dict, Any
from datetime import datetime
import re
import logging

# Import from parent
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from sources.rss_fetcher import Article

logger = logging.getLogger(__name__)


def calculate_topic_score(article: Article, topics_config: Union[Dict, List], text_lower: str = None, keywords_preprocessed: bool = False) -> tuple[float, str]:
    """
    Calculate topic relevance score and classify article.

    Args:
        article: Article to score
        topics_config: Topics configuration dictionary or list
        text_lower: Pre-lowercased text content (optional)
        keywords_preprocessed: If True, assumes keywords in config are already lowercase

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

        # Build text for matching (handle None values) if not provided
        if text_lower is None:
            title = article.title or ""
            summary = article.summary or ""
            text = f"{title} {summary}".lower()
        else:
            text = text_lower

        best_score = 0.0
        best_category = ""

        # Normalize topics_config to a list of dicts for iteration
        iterator = []
        if isinstance(topics_config, dict):
            for cat, cfg in topics_config.items():
                if cfg:
                    # Legacy dict format: config is the dict with keywords/boost
                    item = cfg.copy()
                    item['category'] = cat # Ensure category is set
                    iterator.append(item)
        elif isinstance(topics_config, list):
            iterator = topics_config

        for config in iterator:
            if not config:
                continue

            keywords = config.get('keywords', [])
            if not keywords:
                continue

            # Support both 'priority' (list) and 'priority_boost' (dict) keys
            boost = config.get('priority', config.get('priority_boost', 1.0))

            # Validate boost
            try:
                boost = float(boost)
            except (ValueError, TypeError):
                # Only log warning if we haven't logged it for this category/config before?
                # To avoid spam, just default to 1.0
                boost = 1.0

            # Count keyword matches
            if keywords_preprocessed:
                matches = sum(1 for kw in keywords if kw and kw in text)
            else:
                matches = sum(1 for kw in keywords if kw and kw.lower() in text)

            if matches > 0:
                category_score = matches * boost
                # Use category from config, or fallback to name, or empty
                category_name = config.get('category', config.get('name', ''))

                if category_score > best_score:
                    best_score = category_score
                    best_category = category_name

        return best_score, best_category

    except Exception as e:
        logger.error(f"Error in calculate_topic_score: {e}")
        return 0.0, ""


def calculate_canadian_score(article: Article, canadian_keywords: List[str], boost: float, text_lower: str = None) -> float:
    """
    Calculate Canadian content relevance boost.
    """
    if text_lower is None:
        text = f"{article.title} {article.summary}".lower()
    else:
        text = text_lower
    
    # Check if keywords are likely pre-lowercased?
    # We'll just assume they need lowercasing unless we want to add another arg.
    # For now, let's keep it simple and lower them.
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


def should_exclude(article: Article, exclude_patterns: List[str], text_lower: str = None) -> bool:
    """
    Check if article should be excluded based on patterns.
    """
    if text_lower is None:
        text = f"{article.title} {article.summary}".lower()
    else:
        text = text_lower
    
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
    # Pre-process topics for performance
    processed_topics = []
    raw_topics = config.get('topics', [])

    if isinstance(raw_topics, dict):
        for category, topic_config in raw_topics.items():
            if not topic_config: continue
            processed_topics.append({
                'category': category,
                'keywords': [k.lower() for k in topic_config.get('keywords', []) if k],
                'priority': float(topic_config.get('priority_boost', 1.0))
            })
    elif isinstance(raw_topics, list):
        for topic in raw_topics:
            if not topic: continue
            processed_topics.append({
                'category': topic.get('category', topic.get('name', '')),
                'keywords': [k.lower() for k in topic.get('keywords', []) if k],
                'priority': float(topic.get('priority', 1.0))
            })

    canadian_keywords = config.get('canadian_keywords', [])
    canadian_boost = config.get('canadian_boost', 1.5)
    exclude_patterns = config.get('exclude_patterns', [])
    
    scored_articles = []
    
    for article in articles:
        # Pre-calculate text content once
        title = article.title or ""
        summary = article.summary or ""
        text_lower = f"{title} {summary}".lower()

        # Check exclusions
        if should_exclude(article, exclude_patterns, text_lower=text_lower):
            continue
            
        # Calculate component scores
        # Use processed_topics and optimized flag
        topic_score, category = calculate_topic_score(
            article,
            processed_topics,
            text_lower=text_lower,
            keywords_preprocessed=True
        )

        canadian_multiplier = calculate_canadian_score(
            article,
            canadian_keywords,
            canadian_boost,
            text_lower=text_lower
        )
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
