"""
Review Service - High-level operations for review and curation workflow.

Coordinates between:
- ArticleService (fetching/scoring)
- ReviewRepository (persistence)
- Newsletter generation
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from repositories.review_repository import ReviewRepository
from .article_service import ArticleService

logger = logging.getLogger(__name__)


class ReviewService:
    """Service for managing the review and curation workflow."""

    def __init__(self, config: Dict[str, Any], output_dir: Path):
        """
        Initialize review service.

        Args:
            config: Configuration dictionary
            output_dir: Output directory for storing reviews
        """
        self.config = config
        self.output_dir = output_dir
        self.article_service = ArticleService(config, output_dir=output_dir)
        self.repository = ReviewRepository(output_dir)
        logger.debug("ReviewService initialized")

    def fetch_and_create_review(self, use_cache: bool = True,
                               apply_personalization: bool = False) -> Dict[str, Any]:
        """
        Fetch articles and create a review for curation.

        Args:
            use_cache: Use cached articles if available
            apply_personalization: Apply personalization scores if available (set to False for speed)

        Returns:
            Review data with articles grouped by category
        """
        try:
            logger.info("Starting fetch and review creation")

            # Fetch and score articles
            articles = self.article_service.fetch_and_score_articles(use_cache=use_cache)
            if not articles:
                logger.warning("No articles available for review")
                return self._create_empty_review()

            logger.info(f"Fetched {len(articles)} articles")

            # Categorize articles (personalization skipped for speed on initial fetch)
            categories = self.article_service.categorize_articles(
                articles, apply_personalization=apply_personalization
            )

            # Create review structure
            review_data = self.repository.create_review(
                [art for cat_arts in categories.values() for art in cat_arts]
            )
            review_data['categories'] = categories

            # Add preference profile if personalization service has cached data
            if apply_personalization:
                profile = self.article_service.get_preference_profile()
                if profile:
                    review_data['preference_profile'] = profile
                    logger.info(f"Added preference profile to review")

            logger.info(f"Created review with {len(articles)} articles in {len(categories)} categories")

            # Save review
            self.repository.save_review(review_data)

            return review_data

        except Exception as e:
            logger.error(f"Error in fetch_and_create_review: {e}")
            raise

    def load_review(self) -> Optional[Dict[str, Any]]:
        """
        Load today's review data.

        Returns:
            Review data or None if not available
        """
        try:
            review_data = self.repository.load_review()
            if review_data:
                logger.info(f"Loaded review with {len(review_data.get('categories', {}))} categories")
            else:
                logger.info("No review found for today")
            return review_data
        except Exception as e:
            logger.error(f"Error loading review: {e}")
            return None

    def save_selections(self, selected_ids: List[str]) -> Tuple[bool, int]:
        """
        Save article selections to review.

        Args:
            selected_ids: List of selected article IDs (format: "category:id")

        Returns:
            Tuple of (success, count of selected articles)
        """
        try:
            # Load current review
            review_data = self.repository.load_review()
            if not review_data:
                logger.error("No review data to save selections to")
                return False, 0

            # Update selections
            review_data = self.repository.update_selections(review_data, selected_ids)
            selected_count = len(review_data.get('selected', []))

            # Save updated review
            success = self.repository.save_review(review_data)

            if success:
                logger.info(f"Saved {selected_count} article selections")

            return success, selected_count

        except Exception as e:
            logger.error(f"Error saving selections: {e}")
            return False, 0

    def get_selected_articles(self) -> List[Dict[str, Any]]:
        """
        Get selected articles from current review.

        Returns:
            List of selected article dictionaries
        """
        try:
            review_data = self.repository.load_review()
            if not review_data:
                return []

            selected = review_data.get('selected', [])
            logger.debug(f"Retrieved {len(selected)} selected articles")
            return selected

        except Exception as e:
            logger.error(f"Error getting selected articles: {e}")
            return []

    def clear_review(self) -> bool:
        """
        Clear today's review data.

        Returns:
            True if successful
        """
        try:
            success = self.repository.delete_review()
            if success:
                logger.info("Cleared review data")
            return success
        except Exception as e:
            logger.error(f"Error clearing review: {e}")
            return False

    def get_review_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for current review.

        Returns:
            Dictionary with review statistics
        """
        try:
            review_data = self.repository.load_review()
            if not review_data:
                return {
                    'has_review': False,
                    'total_articles': 0,
                    'categories': 0,
                    'selected': 0
                }

            categories = review_data.get('categories', {})
            selected = review_data.get('selected', [])

            return {
                'has_review': True,
                'date': review_data.get('date', 'unknown'),
                'total_articles': review_data.get('total_articles', 0),
                'categories': len(categories),
                'selected': len(selected),
                'category_names': list(categories.keys())
            }

        except Exception as e:
            logger.error(f"Error getting review summary: {e}")
            return {'has_review': False}

    def _create_empty_review(self) -> Dict[str, Any]:
        """Create an empty review structure."""
        return {
            "date": "",
            "total_articles": 0,
            "categories": {},
            "selected": []
        }
