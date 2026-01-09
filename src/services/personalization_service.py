"""
Personalization Service - Learns from historical selections to personalize article scoring.

Analyzes past newsletter reviews to build a preference profile that includes:
- Favorite sources (weighted by selection frequency)
- Favorite categories (weighted by selection frequency)
- Preferred score ranges
- Keywords that appear in selected articles

Uses this profile to boost article scores and predict selection likelihood.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from collections import Counter
import json

logger = logging.getLogger(__name__)


class PreferenceProfile:
    """User preference profile built from historical selections."""

    def __init__(self):
        """Initialize empty preference profile."""
        self.source_preferences: Dict[str, float] = {}  # source -> boost multiplier
        self.category_preferences: Dict[str, float] = {}  # category -> boost multiplier
        self.keyword_preferences: Dict[str, int] = {}  # keyword -> frequency
        self.score_threshold: float = 0.0  # minimum score of selected articles
        self.score_range: Tuple[float, float] = (0.0, 10.0)  # min/max scores
        self.total_selections: int = 0
        self.total_available: int = 0
        self.selection_rate: float = 0.0
        self.preferred_categories: List[str] = []
        self.preferred_sources: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "source_preferences": self.source_preferences,
            "category_preferences": self.category_preferences,
            "keyword_preferences": self.keyword_preferences,
            "score_threshold": self.score_threshold,
            "score_range": self.score_range,
            "total_selections": self.total_selections,
            "total_available": self.total_available,
            "selection_rate": self.selection_rate,
            "preferred_categories": self.preferred_categories,
            "preferred_sources": self.preferred_sources,
        }


class PersonalizationService:
    """Service for learning from historical selections and personalizing scores."""

    def __init__(self, output_dir: Path):
        """
        Initialize personalization service.

        Args:
            output_dir: Directory containing review_YYYY-MM-DD.json files
        """
        self.output_dir = Path(output_dir)
        self.preference_profile = PreferenceProfile()
        logger.debug("PersonalizationService initialized")

    def analyze_historical_selections(self) -> PreferenceProfile:
        """
        Analyze all past review files to build preference profile.

        Returns:
            PreferenceProfile with learned preferences
        """
        try:
            logger.info("Analyzing historical selections")
            review_files = list(self.output_dir.glob("review_*.json"))

            if not review_files:
                logger.warning("No review files found for analysis")
                return self.preference_profile

            # Collect all selections and metadata
            all_selected_articles = []
            all_available_articles = []
            source_selections = Counter()
            category_selections = Counter()
            all_keywords = Counter()
            scores = []

            for review_file in sorted(review_files):
                try:
                    with open(review_file, 'r', encoding='utf-8') as f:
                        review_data = json.load(f)
                except Exception as e:
                    logger.warning(f"Error reading {review_file}: {e}")
                    continue

                # Get all available articles
                categories = review_data.get('categories', {})
                for category, articles in categories.items():
                    if isinstance(articles, list):
                        all_available_articles.extend(articles)

                # Get selected articles
                selected = review_data.get('selected', [])
                if selected:
                    all_selected_articles.extend(selected)

                    # Track selections by source and category
                    for article in selected:
                        source = article.get('source', 'unknown')
                        source_selections[source] += 1

                        category = article.get('category', 'uncategorized')
                        category_selections[category] += 1

                        # Extract keywords from title
                        title = article.get('title', '')
                        keywords = self._extract_keywords(title)
                        all_keywords.update(keywords)

                        score = article.get('score', 0.0)
                        if isinstance(score, (int, float)):
                            scores.append(score)

            # Build preference profile
            total_selections = len(all_selected_articles)
            total_available = len(all_available_articles)

            self.preference_profile.total_selections = total_selections
            self.preference_profile.total_available = total_available
            self.preference_profile.selection_rate = (
                total_selections / total_available if total_available > 0 else 0.0
            )

            # Score thresholds
            if scores:
                self.preference_profile.score_threshold = min(scores)
                self.preference_profile.score_range = (min(scores), max(scores))

            # Normalize source preferences (higher = more selected)
            if source_selections:
                max_source_count = max(source_selections.values())
                for source, count in source_selections.items():
                    # Boost multiplier: 1.0-2.0x based on selection frequency
                    boost = 1.0 + (count / max_source_count)
                    self.preference_profile.source_preferences[source] = boost

                # Top sources
                self.preference_profile.preferred_sources = [
                    source for source, _ in source_selections.most_common(5)
                ]

            # Normalize category preferences
            if category_selections:
                max_category_count = max(category_selections.values())
                for category, count in category_selections.items():
                    boost = 1.0 + (count / max_category_count)
                    self.preference_profile.category_preferences[category] = boost

                # Top categories
                self.preference_profile.preferred_categories = [
                    cat for cat, _ in category_selections.most_common(5)
                ]

            # Store top keywords
            self.preference_profile.keyword_preferences = dict(all_keywords.most_common(20))

            logger.info(
                f"Analyzed {len(review_files)} reviews: "
                f"{total_selections}/{total_available} selections ({self.preference_profile.selection_rate:.1%})"
            )
            logger.info(f"Top sources: {self.preference_profile.preferred_sources}")
            logger.info(f"Top categories: {self.preference_profile.preferred_categories}")

            return self.preference_profile

        except Exception as e:
            logger.error(f"Error analyzing historical selections: {e}")
            return self.preference_profile

    def boost_article_score(self, article: Dict[str, Any], profile: Optional[PreferenceProfile] = None) -> float:
        """
        Calculate boosted score for an article based on preference profile.

        Args:
            article: Article dictionary with source, category, title, score
            profile: PreferenceProfile to use (uses self.preference_profile if None)

        Returns:
            Boosted score (original + boosts)
        """
        if profile is None:
            profile = self.preference_profile

        original_score = article.get('score', 0.0)
        if not isinstance(original_score, (int, float)):
            original_score = 0.0

        boost = 0.0

        # Source boost
        source = article.get('source', '')
        if source in profile.source_preferences:
            source_multiplier = profile.source_preferences[source]
            source_boost = (source_multiplier - 1.0) * original_score
            boost += source_boost

        # Category boost
        category = article.get('category', '')
        if category in profile.category_preferences:
            category_multiplier = profile.category_preferences[category]
            category_boost = (category_multiplier - 1.0) * original_score
            boost += category_boost

        # Keyword boost
        title = article.get('title', '').lower()
        for keyword, frequency in profile.keyword_preferences.items():
            if keyword.lower() in title:
                keyword_boost = frequency * 0.1  # 0.1-2.0 boost per keyword
                boost += keyword_boost

        boosted_score = original_score + boost
        return round(boosted_score, 2)

    def predict_selection_likelihood(self, article: Dict[str, Any],
                                    profile: Optional[PreferenceProfile] = None) -> int:
        """
        Predict likelihood (0-100%) that user will select this article.

        Args:
            article: Article to evaluate
            profile: PreferenceProfile to use

        Returns:
            Predicted likelihood percentage (0-100)
        """
        if profile is None:
            profile = self.preference_profile

        if profile.total_selections == 0:
            # No historical data, return neutral
            return 50

        score = article.get('score', 0.0)
        if not isinstance(score, (int, float)):
            score = 0.0

        # Base likelihood from score comparison to historical threshold
        min_score, max_score = profile.score_range
        score_range = max_score - min_score if max_score > min_score else 1.0

        # Articles within preferred score range have higher likelihood
        if profile.score_threshold > 0:
            score_normalized = (score - profile.score_threshold) / (10.0 - profile.score_threshold)
            base_likelihood = max(0, min(100, score_normalized * 80))
        else:
            base_likelihood = 50

        # Boost for preferred source
        source = article.get('source', '')
        if source in profile.preferred_sources:
            base_likelihood += 10

        # Boost for preferred category
        category = article.get('category', '')
        if category in profile.preferred_categories:
            base_likelihood += 10

        # Boost for keywords
        title = article.get('title', '').lower()
        keyword_boost = 0
        for keyword in profile.keyword_preferences.keys():
            if keyword.lower() in title:
                keyword_boost += 2

        base_likelihood += min(keyword_boost, 10)  # Cap at 10%

        return max(0, min(100, int(base_likelihood)))

    def get_recommended_articles(self, articles: List[Dict[str, Any]], count: int = 8,
                               profile: Optional[PreferenceProfile] = None) -> List[Dict[str, Any]]:
        """
        Get recommended articles sorted by predicted selection likelihood.

        Args:
            articles: List of articles to recommend from
            count: Number of recommendations to return
            profile: PreferenceProfile to use

        Returns:
            Top N articles most likely to be selected, with predictions added
        """
        if profile is None:
            profile = self.preference_profile

        if not articles or profile.total_selections == 0:
            return articles[:count]

        # Score all articles with predictions
        scored = []
        for article in articles:
            likelihood = self.predict_selection_likelihood(article, profile)
            boosted_score = self.boost_article_score(article, profile)
            scored.append({
                **article,
                "predicted_likelihood": likelihood,
                "boosted_score": boosted_score,
            })

        # Sort by likelihood (descending)
        sorted_articles = sorted(scored, key=lambda a: a['predicted_likelihood'], reverse=True)

        return sorted_articles[:count]

    def get_auto_suggestions(self, articles: List[Dict[str, Any]], threshold: int = 75,
                           profile: Optional[PreferenceProfile] = None) -> List[Dict[str, Any]]:
        """
        Get auto-suggested articles that match user preferences with high confidence.

        Args:
            articles: List of articles to evaluate
            threshold: Likelihood threshold (0-100) for auto-suggestions
            profile: PreferenceProfile to use

        Returns:
            Articles with predicted_likelihood >= threshold
        """
        if profile is None:
            profile = self.preference_profile

        if profile.total_selections == 0:
            return []

        suggestions = []
        for article in articles:
            likelihood = self.predict_selection_likelihood(article, profile)
            if likelihood >= threshold:
                suggestions.append({
                    **article,
                    "predicted_likelihood": likelihood,
                    "boosted_score": self.boost_article_score(article, profile),
                })

        # Sort by likelihood
        return sorted(suggestions, key=lambda a: a['predicted_likelihood'], reverse=True)

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract significant keywords from text.

        Args:
            text: Text to extract keywords from

        Returns:
            List of keywords
        """
        # Simple keyword extraction: words > 4 chars, excluding common words
        stopwords = {
            'the', 'and', 'with', 'from', 'this', 'that', 'will', 'have',
            'been', 'are', 'your', 'more', 'about', 'into', 'than', 'just',
            'which', 'some', 'would', 'could', 'should', 'their', 'after',
            'where', 'what', 'when', 'these', 'other', 'very', 'between'
        }

        words = text.lower().split()
        keywords = [
            w.strip('.,!?;:"\'')
            for w in words
            if len(w.strip('.,!?;:"\'')) > 4 and w.lower() not in stopwords
        ]
        return keywords

    def get_preference_profile_summary(self) -> str:
        """
        Get human-readable summary of preference profile.

        Returns:
            Formatted string describing user preferences
        """
        profile = self.preference_profile

        summary = []
        summary.append(f"=== User Preference Profile ===")
        summary.append(f"Historical Data: {profile.total_selections}/{profile.total_available} selections ({profile.selection_rate:.1%})")
        summary.append(f"Preferred Score Range: {profile.score_range[0]:.1f} - {profile.score_range[1]:.1f}")
        summary.append(f"Selection Threshold: {profile.score_threshold:.1f}")

        if profile.preferred_sources:
            summary.append(f"Top Sources: {', '.join(profile.preferred_sources[:3])}")

        if profile.preferred_categories:
            summary.append(f"Top Categories: {', '.join(profile.preferred_categories[:3])}")

        if profile.keyword_preferences:
            top_keywords = list(profile.keyword_preferences.keys())[:5]
            summary.append(f"Common Keywords: {', '.join(top_keywords)}")

        return '\n'.join(summary)
