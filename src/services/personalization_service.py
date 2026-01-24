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
        self._analysis_cached = False
        self._cache_time = None
        logger.debug("PersonalizationService initialized")

    def is_profile_cached(self) -> bool:
        """Check if preference profile has been analyzed."""
        return self._analysis_cached

    def clear_cache(self) -> None:
        """
        Clear cached preference profile in memory.

        Note: This does not remove the persistent cache file.
        To force a rebuild, delete the profile_cache.json file manually.
        """
        self._analysis_cached = False
        self._cache_time = None
        self.preference_profile = PreferenceProfile()
        logger.debug("Personalization memory cache cleared")

    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """Load cached profile stats."""
        cache_file = self.output_dir / "profile_cache.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert dicts back to Counters where appropriate
            if 'stats' in data:
                stats = data['stats']
                if 'source_selections' in stats:
                    stats['source_selections'] = Counter(stats['source_selections'])
                if 'category_selections' in stats:
                    stats['category_selections'] = Counter(stats['category_selections'])
                if 'all_keywords' in stats:
                    stats['all_keywords'] = Counter(stats['all_keywords'])

            return data
        except Exception as e:
            logger.warning(f"Error reading profile cache: {e}")
            return None

    def _save_cache(self, processed_files: List[str], stats: Dict[str, Any]) -> None:
        """Save profile stats to cache."""
        cache_file = self.output_dir / "profile_cache.json"

        try:
            data = {
                'processed_files': processed_files,
                'stats': stats,
                'last_updated': datetime.now().isoformat()
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Error saving profile cache: {e}")

    def _process_review_file(self, review_file: Path) -> Optional[Dict[str, Any]]:
        """
        Process a single review file to extract stats.

        Args:
            review_file: Path to the review file

        Returns:
            Dictionary with extracted stats (counters, lists) or None on error
        """
        try:
            with open(review_file, 'r', encoding='utf-8') as f:
                review_data = json.load(f)
        except Exception as e:
            logger.warning(f"Error reading {review_file}: {e}")
            return None

        stats = {
            'selected_count': 0,
            'available_count': 0,
            'source_selections': Counter(),
            'category_selections': Counter(),
            'all_keywords': Counter(),
            'scores': []
        }

        # Get all available articles
        categories = review_data.get('categories', {})
        for category, articles in categories.items():
            if isinstance(articles, list):
                stats['available_count'] += len(articles)

        # Get selected articles
        selected = review_data.get('selected', [])
        if selected:
            stats['selected_count'] = len(selected)

            # Track selections by source and category
            for article in selected:
                source = article.get('source', 'unknown')
                stats['source_selections'][source] += 1

                category = article.get('category', 'uncategorized')
                stats['category_selections'][category] += 1

                # Extract keywords from title
                title = article.get('title', '')
                keywords = self._extract_keywords(title)
                stats['all_keywords'].update(keywords)

                score = article.get('score', 0.0)
                if isinstance(score, (int, float)):
                    stats['scores'].append(score)

        return stats

    def _build_profile_from_stats(self, stats: Dict[str, Any]) -> PreferenceProfile:
        """
        Build PreferenceProfile from aggregated stats.

        Args:
            stats: Dictionary with aggregated counters and lists

        Returns:
            PreferenceProfile
        """
        profile = PreferenceProfile()

        total_selections = stats.get('total_selections', 0)
        total_available = stats.get('total_available', 0)

        profile.total_selections = total_selections
        profile.total_available = total_available
        profile.selection_rate = (
            total_selections / total_available if total_available > 0 else 0.0
        )

        scores_min = stats.get('scores_min')
        scores_max = stats.get('scores_max')

        if scores_min is not None and scores_max is not None:
             profile.score_threshold = scores_min
             profile.score_range = (scores_min, scores_max)

        source_selections = stats.get('source_selections', Counter())
        if source_selections:
            max_source_count = max(source_selections.values())
            for source, count in source_selections.items():
                # Boost multiplier: 1.0-2.0x based on selection frequency
                boost = 1.0 + (count / max_source_count)
                profile.source_preferences[source] = boost

            profile.preferred_sources = [
                source for source, _ in source_selections.most_common(5)
            ]

        category_selections = stats.get('category_selections', Counter())
        if category_selections:
            max_category_count = max(category_selections.values())
            for category, count in category_selections.items():
                boost = 1.0 + (count / max_category_count)
                profile.category_preferences[category] = boost

            profile.preferred_categories = [
                cat for cat, _ in category_selections.most_common(5)
            ]

        all_keywords = stats.get('all_keywords', Counter())
        profile.keyword_preferences = dict(all_keywords.most_common(20))

        return profile

    def analyze_historical_selections(self) -> PreferenceProfile:
        """
        Analyze all past review files to build preference profile.

        Returns:
            PreferenceProfile with learned preferences
        """
        try:
            logger.info("Analyzing historical selections")

            # Load cache
            cache_data = self._load_cache()
            cached_files = set(cache_data['processed_files']) if cache_data else set()
            aggregated_stats = cache_data['stats'] if cache_data else {
                'total_selections': 0,
                'total_available': 0,
                'source_selections': Counter(),
                'category_selections': Counter(),
                'all_keywords': Counter(),
                'scores_min': None,
                'scores_max': None
            }

            review_files = list(self.output_dir.glob("review_*.json"))
            if not review_files:
                logger.warning("No review files found for analysis")
                return self.preference_profile

            current_files = {f.name for f in review_files}
            new_files = [f for f in review_files if f.name not in cached_files]

            # Check if any cached file is missing (rebuild if so)
            missing_files = cached_files - current_files
            if missing_files:
                logger.info(f"Found {len(missing_files)} deleted files, rebuilding cache...")
                # Reset stats and process all files
                aggregated_stats = {
                    'total_selections': 0,
                    'total_available': 0,
                    'source_selections': Counter(),
                    'category_selections': Counter(),
                    'all_keywords': Counter(),
                    'scores_min': None,
                    'scores_max': None
                }
                new_files = review_files
                cached_files = set()

            if not new_files and not missing_files:
                logger.info("Using cached profile stats")
                self.preference_profile = self._build_profile_from_stats(aggregated_stats)
                self._analysis_cached = True
                self._cache_time = datetime.now()
                return self.preference_profile

            # Process new files
            logger.info(f"Processing {len(new_files)} new review files")

            new_scores = []

            for review_file in sorted(new_files):
                file_stats = self._process_review_file(review_file)
                if not file_stats:
                    continue

                aggregated_stats['total_selections'] += file_stats['selected_count']
                aggregated_stats['total_available'] += file_stats['available_count']
                aggregated_stats['source_selections'].update(file_stats['source_selections'])
                aggregated_stats['category_selections'].update(file_stats['category_selections'])
                aggregated_stats['all_keywords'].update(file_stats['all_keywords'])
                new_scores.extend(file_stats['scores'])

            if new_scores:
                current_min = aggregated_stats.get('scores_min')
                current_max = aggregated_stats.get('scores_max')

                batch_min = min(new_scores)
                batch_max = max(new_scores)

                if current_min is None:
                    aggregated_stats['scores_min'] = batch_min
                else:
                    aggregated_stats['scores_min'] = min(current_min, batch_min)

                if current_max is None:
                    aggregated_stats['scores_max'] = batch_max
                else:
                    aggregated_stats['scores_max'] = max(current_max, batch_max)

            # Build profile
            self.preference_profile = self._build_profile_from_stats(aggregated_stats)

            # Save cache
            all_processed_files = list(cached_files | {f.name for f in new_files})
            self._save_cache(all_processed_files, aggregated_stats)

            # Mark as cached
            self._analysis_cached = True
            from datetime import datetime as dt
            self._cache_time = dt.now()

            logger.info(
                f"Analyzed {len(review_files)} reviews: "
                f"{self.preference_profile.total_selections}/{self.preference_profile.total_available} selections ({self.preference_profile.selection_rate:.1%})"
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
