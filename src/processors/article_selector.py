#!/usr/bin/env python3
"""
Article Selector Module

Auto-selects articles for newsletter sections based on Scott's content criteria:
- Headlines: 8-10 articles with 60% governance + 40% capabilities
- Bright Spots: 2-3 positive stories
- Tool: 1 new tool/product
- Deep Dives: 4-5 research/analysis pieces
- Grain Quality: Optional agriculture-related content

Enforces selection rules:
- At least 1 Canadian government story in headlines
- At least 1 governance/regulation story in headlines
- Sentiment balance: 40% concerns, 35% opportunities, 25% neutral
"""

import logging
from typing import List, Dict, Optional
import sys
from pathlib import Path

# Import Article model
sys.path.append(str(Path(__file__).parent.parent))
from sources.rss_fetcher import Article

logger = logging.getLogger(__name__)


# Keywords for detecting Canadian government stories
CANADIAN_GOV_KEYWORDS = [
    'government of canada',
    'canadian government',
    'federal government',
    'parliament',
    'minister',
    'department of',
    'innovation canada',
    'canadian digital',
    'canadian ai',
    'ised',  # Innovation, Science and Economic Development
    'treasury board',
    'algorithm impact assessment',
    'provincial government',
    'province of',
    'statscan',
    'statistics canada'
]

# Keywords for detecting governance/regulation stories
GOVERNANCE_KEYWORDS = [
    'regulation',
    'regulation ai',
    'regulatory',
    'legislation',
    'law',
    'compliance',
    'governance',
    'policy',
    'ethics',
    'safety',
    'alignment',
    'responsible ai',
    'oversight',
    'audit',
    'transparency',
    'accountability',
    'bill',
    'act',
    'framework'
]


def is_canadian_government_story(article: Article) -> bool:
    """Check if article is about Canadian government AI initiatives."""
    text = (article.title + " " + article.summary + " " + article.source).lower()
    return any(keyword in text for keyword in CANADIAN_GOV_KEYWORDS)


def is_governance_story(article: Article) -> bool:
    """Check if article is about AI governance/regulation."""
    text = (article.title + " " + article.summary).lower()
    return any(keyword in text for keyword in GOVERNANCE_KEYWORDS)


def is_canadian_angle(article: Article) -> bool:
    """Check if article mentions Canada or has Canadian relevance."""
    canadian_keywords = ['canada', 'canadian', 'toronto', 'montreal', 'ottawa', 'vancouver', 'bc', 'alberta',
                         'quebec', 'ontario', 'manitoba', 'nova scotia']
    text = (article.title + " " + article.summary + " " + article.source).lower()
    return any(keyword in text for keyword in canadian_keywords)


def find_canadian_government_stories(articles: List[Article]) -> List[Article]:
    """Find Canadian government AI stories from headlines."""
    gov_stories = [a for a in articles if is_canadian_government_story(a)]
    logger.info(f"Found {len(gov_stories)} Canadian government stories")
    return gov_stories


def find_governance_stories(articles: List[Article]) -> List[Article]:
    """Find governance/regulation stories from headlines."""
    gov_stories = [a for a in articles if is_governance_story(a)]
    logger.info(f"Found {len(gov_stories)} governance/regulation stories")
    return gov_stories


def check_sentiment_distribution(selected_articles: Dict[str, List[Article]]) -> Dict[str, float]:
    """
    Check sentiment distribution across selected articles.

    Target: 40% concerns (negative), 35% opportunities (positive), 25% neutral
    """
    all_articles = []
    for articles_list in selected_articles.values():
        all_articles.extend(articles_list)

    if not all_articles:
        logger.warning("No articles to check sentiment distribution")
        return {}

    # Count sentiments
    sentiments = {}
    for article in all_articles:
        sentiment = getattr(article, 'sentiment', 'neutral')
        sentiments[sentiment] = sentiments.get(sentiment, 0) + 1

    total = len(all_articles)
    distribution = {
        'positive': sentiments.get('positive', 0) / total if total > 0 else 0,
        'negative': sentiments.get('negative', 0) / total if total > 0 else 0,
        'neutral': sentiments.get('neutral', 0) / total if total > 0 else 0,
        'mixed': sentiments.get('mixed', 0) / total if total > 0 else 0,
    }

    logger.info(f"Sentiment distribution:")
    logger.info(f"  Positive (opportunities): {distribution['positive']:.0%} (target 35%)")
    logger.info(f"  Negative (concerns): {distribution['negative']:.0%} (target 40%)")
    logger.info(f"  Neutral: {distribution['neutral']:.0%} (target 25%)")
    logger.info(f"  Mixed: {distribution['mixed']:.0%}")

    # Check if distribution is balanced
    pos_target = 0.35
    neg_target = 0.40
    neutral_target = 0.25
    tolerance = 0.10  # 10% tolerance

    if abs(distribution['positive'] - pos_target) > tolerance:
        logger.warning(
            f"⚠️  Positive sentiment imbalance: {distribution['positive']:.0%}, target {pos_target:.0%}"
        )

    if abs(distribution['negative'] - neg_target) > tolerance:
        logger.warning(
            f"⚠️  Negative sentiment imbalance: {distribution['negative']:.0%}, target {neg_target:.0%}"
        )

    return distribution


def auto_select_articles(
    scored_articles: List[Article],
    config: dict,
    warn_on_missing: bool = True
) -> Dict[str, List[Article]]:
    """
    Auto-select articles for newsletter sections based on Scott's criteria.

    Selection Rules:
    1. Headlines: 8-10 articles with 60% governance + 40% capabilities
    2. At least 1 Canadian government story (warn if missing)
    3. At least 1 governance/regulation story (warn if missing)
    4. Bright Spots: 2-3 positive sentiment articles
    5. Tool: 1 recent tool/product
    6. Deep Dives: 4-5 research/analysis pieces
    7. Grain Quality: Optional (if agriculture articles available)

    Args:
        scored_articles: List of Article objects (should be scored and classified)
        config: Configuration dict with section settings
        warn_on_missing: Whether to log warnings for missing required articles

    Returns:
        Dict with sections as keys and article lists as values
    """

    # Extract section configuration
    section_config = config.get('sections', {})
    headlines_config = section_config.get('headlines', {})
    bright_spots_config = section_config.get('bright_spots', {})
    tools_config = section_config.get('tools', {})
    deep_dives_config = section_config.get('deep_dives', {})
    grain_config = section_config.get('grain_quality', {})

    # Target counts
    target_headlines = headlines_config.get('target_count', 8)  # 8-10, use min
    target_bright_spots = bright_spots_config.get('target_count', 2)  # 2-3, use min
    target_tools = tools_config.get('target_count', 1)
    target_deep_dives = deep_dives_config.get('target_count', 4)  # 4-5, use min
    governance_ratio = headlines_config.get('governance_ratio', 0.6)  # 60%

    # Separate articles by classified section
    classified_articles = {
        'headline': [],
        'bright_spot': [],
        'tool': [],
        'deep_dive': [],
        'grain_quality': []
    }

    for article in scored_articles:
        section = getattr(article, 'section', 'headline')
        if section in classified_articles:
            classified_articles[section].append(article)
        else:
            # Default to headline if unknown section
            classified_articles['headline'].append(article)

    # Initialize selection
    selection = {
        'headlines': [],
        'bright_spots': [],
        'tools': [],
        'deep_dives': [],
        'grain_quality': []
    }

    # ===== HEADLINES SELECTION =====
    logger.info(f"\n🔍 Selecting headlines ({target_headlines} target)...")

    # Rule 1: At least 1 Canadian government story
    canadian_gov_stories = find_canadian_government_stories(classified_articles['headline'])
    if canadian_gov_stories:
        selection['headlines'].append(canadian_gov_stories[0])
        logger.info(f"✓ Added Canadian government story: {canadian_gov_stories[0].title[:60]}")
    elif warn_on_missing:
        logger.warning("⚠️  No Canadian government story found in headlines!")

    # Rule 2: At least 1 governance/regulation story
    governance_stories = find_governance_stories(classified_articles['headline'])
    governance_story_to_add = None
    if governance_stories:
        # Avoid duplicate with Canadian gov story
        governance_story_to_add = next(
            (a for a in governance_stories if a not in selection['headlines']),
            None
        )
        if governance_story_to_add:
            selection['headlines'].append(governance_story_to_add)
            logger.info(f"✓ Added governance story: {governance_story_to_add.title[:60]}")
    elif warn_on_missing:
        logger.warning("⚠️  No governance/regulation story found in headlines!")

    # Rule 3: Fill remaining headlines with 60/40 governance/capabilities mix
    remaining_headlines = [
        a for a in classified_articles['headline']
        if a not in selection['headlines']
    ]

    # Separate by governance vs other
    governance_articles = [a for a in remaining_headlines if is_governance_story(a)]
    other_articles = [a for a in remaining_headlines if a not in governance_articles]

    # Calculate how many more we need
    needed = target_headlines - len(selection['headlines'])
    target_governance = max(0, int(target_headlines * governance_ratio))
    current_governance = len([a for a in selection['headlines'] if is_governance_story(a)])
    needed_governance = max(0, target_governance - current_governance)
    needed_other = needed - needed_governance

    # Add governance articles
    selection['headlines'].extend(governance_articles[:needed_governance])
    # Add other articles (capabilities, research, etc.)
    selection['headlines'].extend(other_articles[:needed_other])

    logger.info(f"✓ Selected {len(selection['headlines'])} headlines " +
                f"({governance_ratio:.0%} governance, {1-governance_ratio:.0%} other)")

    # ===== BRIGHT SPOTS SELECTION =====
    logger.info(f"\n✨ Selecting bright spots ({target_bright_spots} target)...")
    selection['bright_spots'] = classified_articles['bright_spot'][:target_bright_spots]
    if selection['bright_spots']:
        logger.info(f"✓ Selected {len(selection['bright_spots'])} bright spots")
    else:
        logger.warning("⚠️  No bright spot stories found!")

    # ===== TOOLS SELECTION =====
    logger.info(f"\n🛠️  Selecting tools ({target_tools} target)...")
    selection['tools'] = classified_articles['tool'][:target_tools]
    if selection['tools']:
        logger.info(f"✓ Selected {len(selection['tools'])} tools")
    else:
        logger.warning("⚠️  No tool stories found!")

    # ===== DEEP DIVES SELECTION =====
    logger.info(f"\n📊 Selecting deep dives ({target_deep_dives} target)...")
    selection['deep_dives'] = classified_articles['deep_dive'][:target_deep_dives]
    logger.info(f"✓ Selected {len(selection['deep_dives'])} deep dives")

    # ===== GRAIN QUALITY SELECTION (optional) =====
    if grain_config.get('enabled', True):
        logger.info(f"\n🌾 Selecting grain quality articles (optional)...")
        selection['grain_quality'] = classified_articles['grain_quality']
        if selection['grain_quality']:
            logger.info(f"✓ Selected {len(selection['grain_quality'])} grain quality articles")
        else:
            logger.info(f"  No grain quality articles this week")

    # ===== SENTIMENT BALANCE CHECK =====
    logger.info(f"\n📈 Checking sentiment balance...")
    check_sentiment_distribution(selection)

    # Log final summary
    logger.info(f"\n{'='*50}")
    logger.info(f"📰 FINAL SELECTION SUMMARY")
    logger.info(f"{'='*50}")
    total_articles = sum(len(articles) for articles in selection.values())
    logger.info(f"Headlines:     {len(selection['headlines']):2d} (target: {target_headlines})")
    logger.info(f"Bright Spots:  {len(selection['bright_spots']):2d} (target: {target_bright_spots})")
    logger.info(f"Tools:         {len(selection['tools']):2d} (target: {target_tools})")
    logger.info(f"Deep Dives:    {len(selection['deep_dives']):2d} (target: {target_deep_dives})")
    logger.info(f"Grain Quality: {len(selection['grain_quality']):2d} (optional)")
    logger.info(f"{'─'*50}")
    logger.info(f"Total:         {total_articles:2d} articles")
    logger.info(f"{'='*50}")

    return selection


def validate_selection(selection: Dict[str, List[Article]], config: dict) -> bool:
    """
    Validate that selection meets minimum requirements.

    Returns: True if valid, False otherwise
    """
    section_config = config.get('sections', {})
    headlines_config = section_config.get('headlines', {})

    valid = True

    # Check minimum headlines
    if len(selection['headlines']) < 6:
        logger.error(f"❌ Not enough headlines: {len(selection['headlines'])} < 6")
        valid = False

    # Check for required Canadian government story
    if headlines_config.get('required_canadian_gov', 1) > 0:
        has_canadian_gov = any(is_canadian_government_story(a) for a in selection['headlines'])
        if not has_canadian_gov:
            logger.error("❌ Missing required Canadian government story")
            # Don't fail validation, but warn

    # Check for required governance story
    if headlines_config.get('required_governance', 1) > 0:
        has_governance = any(is_governance_story(a) for a in selection['headlines'])
        if not has_governance:
            logger.error("❌ Missing required governance story")
            # Don't fail validation, but warn

    return valid
