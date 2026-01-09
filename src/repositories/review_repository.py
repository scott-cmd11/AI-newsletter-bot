"""
Review Repository - Handles persistence of article reviews and selections.

Manages the JSON file-based storage of:
- Fetched articles grouped by category
- User selections
- Review metadata (date, counts)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class ReviewRepository:
    """Manages persistence of review data (articles and selections)."""

    def __init__(self, output_dir: Path):
        """
        Initialize repository.

        Args:
            output_dir: Directory for storing review files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ReviewRepository initialized with output_dir: {output_dir}")

    def get_review_file(self, date: Optional[str] = None) -> Path:
        """
        Get review file path for a specific date.

        Args:
            date: Date string in YYYY-MM-DD format (default: today)

        Returns:
            Path to review file
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        return self.output_dir / f"review_{date}.json"

    def load_review(self, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Load review data from file.

        Args:
            date: Date string in YYYY-MM-DD format (default: today)

        Returns:
            Review data dictionary or None if file doesn't exist
        """
        review_file = self.get_review_file(date)

        if not review_file.exists():
            logger.debug(f"Review file not found: {review_file}")
            return None

        try:
            with open(review_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"Loaded review from {review_file}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse review file {review_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading review {review_file}: {e}")
            return None

    def save_review(self, review_data: Dict[str, Any], date: Optional[str] = None) -> bool:
        """
        Save review data to file.

        Args:
            review_data: Review data to save
            date: Date string in YYYY-MM-DD format (default: today)

        Returns:
            True if successful, False otherwise
        """
        if not review_data:
            logger.warning("Attempted to save empty review data")
            return False

        review_file = self.get_review_file(date)

        try:
            with open(review_file, 'w', encoding='utf-8') as f:
                json.dump(review_data, f, indent=2, default=str)
            logger.info(f"Saved review to {review_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving review to {review_file}: {e}")
            return False

    def create_review(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a new review structure from articles.

        Args:
            articles: List of article dictionaries grouped by category

        Returns:
            Review data structure
        """
        categories = {}
        total_articles = 0

        for article in articles:
            category = article.get('category', 'uncategorized')
            if category not in categories:
                categories[category] = []
            categories[category].append(article)
            total_articles += 1

        return {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "total_articles": total_articles,
            "categories": categories,
            "selected": []
        }

    def update_selections(self, review_data: Dict[str, Any],
                         selected_ids: List[str]) -> Dict[str, Any]:
        """
        Update article selections in review data.

        Args:
            review_data: Review data to update
            selected_ids: List of selected article IDs in format "category:id"

        Returns:
            Updated review data
        """
        if not review_data:
            logger.warning("Cannot update selections on None review_data")
            return review_data

        # Reset all selections
        for cat_name, articles in review_data.get('categories', {}).items():
            for article in articles:
                article['selected'] = False

        # Mark selected articles
        selected_articles = []
        for sel_id in selected_ids:
            try:
                cat_name, article_id = sel_id.split(':')
                article_id = int(article_id)

                if cat_name in review_data['categories']:
                    for article in review_data['categories'][cat_name]:
                        if article['id'] == article_id:
                            article['selected'] = True
                            article['category'] = cat_name
                            selected_articles.append(article)
                            break
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing selection ID '{sel_id}': {e}")
                continue

        review_data['selected'] = selected_articles
        logger.info(f"Updated selections: {len(selected_articles)} articles selected")
        return review_data

    def delete_review(self, date: Optional[str] = None) -> bool:
        """
        Delete review file for a date.

        Args:
            date: Date string in YYYY-MM-DD format (default: today)

        Returns:
            True if successful, False otherwise
        """
        review_file = self.get_review_file(date)

        try:
            if review_file.exists():
                review_file.unlink()
                logger.info(f"Deleted review file: {review_file}")
            return True
        except Exception as e:
            logger.error(f"Error deleting review {review_file}: {e}")
            return False

    def get_review_file_path(self, date: Optional[str] = None) -> str:
        """Get review file path as string (for logging)."""
        return str(self.get_review_file(date))
