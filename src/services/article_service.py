"""
Article Service - Handles fetching, scoring, and categorizing articles.

Business logic for:
- Fetching articles from configured sources
- Scoring and ranking articles
- Categorizing articles by topic
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from sources.rss_fetcher import Article, fetch_all_articles
from processors.scorer import score_articles
from .personalization_service import PersonalizationService

logger = logging.getLogger(__name__)


class ArticleService:
    """Service for managing articles (fetch, score, categorize)."""

    def __init__(self, config: Dict[str, Any], output_dir: Optional[Path] = None):
        """
        Initialize article service.

        Args:
            config: Configuration dictionary
            output_dir: Optional output directory for personalization
        """
        self.config = config
        self.output_dir = output_dir
        self.personalization_service = None
        if output_dir:
            self.personalization_service = PersonalizationService(output_dir)
            self.personalization_service.analyze_historical_selections()
        logger.debug("ArticleService initialized")

    def fetch_and_score_articles(self, use_cache: bool = True) -> List[Article]:
        """
        Fetch articles from all sources and score them.

        Args:
            use_cache: Use cached articles if available

        Returns:
            List of scored articles sorted by score (highest first)
        """
        try:
            logger.info("Starting article fetch and score process")

            # Fetch articles
            articles = fetch_all_articles(self.config, use_cache=use_cache)
            if not articles:
                logger.warning("No articles fetched")
                return []

            # Score articles
            scored_articles = score_articles(articles, self.config)
            logger.info(f"Fetched and scored {len(scored_articles)} articles")

            return scored_articles

        except Exception as e:
            logger.error(f"Error in fetch_and_score_articles: {e}")
            raise

    def categorize_articles(self, articles: List[Article],
                           apply_personalization: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group articles by category and convert to dictionaries.

        Args:
            articles: List of Article objects
            apply_personalization: Apply personalization scores if available

        Returns:
            Dictionary mapping category names to article lists
        """
        if not articles:
            return {}

        categories = {}

        for article in articles:
            category = article.category or "uncategorized"
            if category not in categories:
                categories[category] = []

            # Convert article to dictionary with ID
            article_dict = {
                "id": len(categories[category]),
                "title": article.title,
                "url": article.url,
                "source": article.source,
                "score": article.score,
                "summary": article.summary[:300] if article.summary else "",
                "published": article.published.isoformat() if article.published else None,
                "selected": False,
                "category": category
            }

            # Apply personalization if available
            if apply_personalization and self.personalization_service:
                article_dict["predicted_likelihood"] = self.personalization_service.predict_selection_likelihood(article_dict)
                article_dict["boosted_score"] = self.personalization_service.boost_article_score(article_dict)

            categories[category].append(article_dict)

        logger.debug(f"Categorized {len(articles)} articles into {len(categories)} categories")
        return categories

    def get_article_by_id(self, categories: Dict[str, List[Dict]],
                          category: str, article_id: int) -> Dict[str, Any]:
        """
        Get a specific article by category and ID.

        Args:
            categories: Categorized articles
            category: Category name
            article_id: Article ID within category

        Returns:
            Article dictionary or None if not found
        """
        if category not in categories:
            return None

        for article in categories[category]:
            if article['id'] == article_id:
                return article

        return None

    def get_top_articles(self, articles: List[Article], count: int = 8) -> List[Article]:
        """
        Get top N articles by score.

        Args:
            articles: List of scored articles
            count: Number of articles to return

        Returns:
            Top N articles
        """
        if not articles:
            return []

        top = articles[:count]
        logger.debug(f"Selected top {len(top)} articles from {len(articles)}")
        return top

    def reconstruct_articles_from_dicts(self,
                                       article_dicts: List[Dict[str, Any]]) -> List[Article]:
        """
        Reconstruct Article objects from dictionaries.

        Used when loading selected articles from review data.

        Args:
            article_dicts: List of article dictionaries

        Returns:
            List of Article objects
        """
        from datetime import datetime

        articles = []
        for a in article_dicts:
            try:
                pub_date = None
                if a.get('published'):
                    try:
                        pub_date = datetime.fromisoformat(a['published'])
                    except (ValueError, TypeError):
                        pass

                article = Article(
                    title=a.get('title', ''),
                    url=a.get('url', ''),
                    source=a.get('source', 'Unknown'),
                    published=pub_date or datetime.now(),
                    summary=a.get('summary', ''),
                    category=a.get('category', ''),
                    score=a.get('score', 0.0)
                )
                articles.append(article)
            except Exception as e:
                logger.warning(f"Error reconstructing article from dict: {e}")
                continue

        logger.debug(f"Reconstructed {len(articles)} Article objects from dictionaries")
        return articles

    def get_personalized_recommendations(self, articles: List[Article],
                                        count: int = 8) -> List[Dict[str, Any]]:
        """
        Get personalized article recommendations based on user preferences.

        Args:
            articles: List of scored articles
            count: Number of recommendations to return

        Returns:
            Top N articles with personalization scores, or empty if personalization unavailable
        """
        if not self.personalization_service:
            logger.warning("Personalization service not initialized")
            return []

        # Convert articles to dictionaries
        article_dicts = [
            {
                "title": a.title,
                "url": a.url,
                "source": a.source,
                "score": a.score,
                "summary": a.summary,
                "category": a.category or "uncategorized",
                "published": a.published.isoformat() if a.published else None,
            }
            for a in articles
        ]

        # Get recommendations
        recommendations = self.personalization_service.get_recommended_articles(
            article_dicts, count=count
        )

        logger.info(f"Generated {len(recommendations)} personalized recommendations")
        return recommendations

    def get_auto_suggestions(self, articles: List[Article],
                           threshold: int = 75) -> List[Dict[str, Any]]:
        """
        Get auto-suggested articles that match user preferences with high confidence.

        Args:
            articles: List of scored articles
            threshold: Likelihood threshold (0-100) for auto-suggestions

        Returns:
            Articles with predicted_likelihood >= threshold
        """
        if not self.personalization_service:
            logger.warning("Personalization service not initialized")
            return []

        # Convert articles to dictionaries
        article_dicts = [
            {
                "title": a.title,
                "url": a.url,
                "source": a.source,
                "score": a.score,
                "summary": a.summary,
                "category": a.category or "uncategorized",
                "published": a.published.isoformat() if a.published else None,
            }
            for a in articles
        ]

        # Get suggestions
        suggestions = self.personalization_service.get_auto_suggestions(
            article_dicts, threshold=threshold
        )

        logger.info(f"Found {len(suggestions)} auto-suggestion candidates (threshold={threshold}%)")
        return suggestions

    def get_preference_profile(self) -> Optional[Dict[str, Any]]:
        """
        Get user preference profile if personalization is available.

        Returns:
            Preference profile dictionary or None
        """
        if self.personalization_service:
            return self.personalization_service.preference_profile.to_dict()
        return None
