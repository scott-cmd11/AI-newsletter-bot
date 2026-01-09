"""Unit tests for service layer."""

import unittest
import tempfile
from datetime import datetime
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sources.rss_fetcher import Article
from services.article_service import ArticleService
from services.newsletter_service import NewsletterService
from services.review_service import ReviewService
from repositories.review_repository import ReviewRepository


class TestArticleService(unittest.TestCase):
    """Test ArticleService."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'topics': [],
            'canadian_boost': 1.0,
            'max_articles': 8
        }
        self.service = ArticleService(self.config)

    def test_categorize_articles(self):
        """Test article categorization."""
        articles = [
            Article(
                title="Article 1",
                url="https://example.com/1",
                source="Test",
                published=datetime.now(),
                summary="Summary",
                category="governance"
            ),
            Article(
                title="Article 2",
                url="https://example.com/2",
                source="Test",
                published=datetime.now(),
                summary="Summary",
                category="governance"
            ),
            Article(
                title="Article 3",
                url="https://example.com/3",
                source="Test",
                published=datetime.now(),
                summary="Summary",
                category="capabilities"
            ),
        ]

        categories = self.service.categorize_articles(articles)

        self.assertIn("governance", categories)
        self.assertIn("capabilities", categories)
        self.assertEqual(len(categories["governance"]), 2)
        self.assertEqual(len(categories["capabilities"]), 1)

    def test_categorize_uncategorized_articles(self):
        """Test that uncategorized articles get 'uncategorized' category."""
        articles = [
            Article(
                title="Article",
                url="https://example.com/1",
                source="Test",
                published=datetime.now(),
                summary="Summary",
                category=""  # No category
            ),
        ]

        categories = self.service.categorize_articles(articles)

        self.assertIn("uncategorized", categories)

    def test_get_top_articles(self):
        """Test getting top N articles."""
        articles = [
            Article(
                title=f"Article {i}",
                url=f"https://example.com/{i}",
                source="Test",
                published=datetime.now(),
                summary="Summary",
                score=float(10 - i)
            )
            for i in range(15)
        ]

        top_5 = self.service.get_top_articles(articles, 5)
        self.assertEqual(len(top_5), 5)

        # Check they're in score order
        for i in range(len(top_5) - 1):
            self.assertGreaterEqual(top_5[i].score, top_5[i+1].score)

    def test_reconstruct_articles_from_dicts(self):
        """Test reconstructing Article objects from dictionaries."""
        article_dicts = [
            {
                "title": "Test Article",
                "url": "https://example.com",
                "source": "Test",
                "published": datetime.now().isoformat(),
                "summary": "Test summary",
                "category": "test",
                "score": 5.0
            }
        ]

        articles = self.service.reconstruct_articles_from_dicts(article_dicts)

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, "Test Article")


class TestReviewRepository(unittest.TestCase):
    """Test ReviewRepository."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo = ReviewRepository(Path(self.temp_dir))

    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_create_review(self):
        """Test creating a review structure."""
        articles = [
            {"title": "Article 1", "category": "test"},
            {"title": "Article 2", "category": "test"},
        ]

        review = self.repo.create_review(articles)

        self.assertIsNotNone(review)
        self.assertEqual(review["total_articles"], 2)
        self.assertIn("test", review["categories"])

    def test_save_and_load_review(self):
        """Test saving and loading review data."""
        review_data = {
            "date": "2024-01-01",
            "total_articles": 5,
            "categories": {"test": []},
            "selected": []
        }

        # Save
        self.repo.save_review(review_data, "2024-01-01")

        # Load
        loaded = self.repo.load_review("2024-01-01")

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["date"], "2024-01-01")
        self.assertEqual(loaded["total_articles"], 5)

    def test_update_selections(self):
        """Test updating article selections."""
        review_data = {
            "date": "2024-01-01",
            "categories": {
                "test": [
                    {"id": 0, "title": "Article 1", "selected": False},
                    {"id": 1, "title": "Article 2", "selected": False},
                ]
            },
            "selected": []
        }

        selected_ids = ["test:0", "test:1"]
        updated = self.repo.update_selections(review_data, selected_ids)

        self.assertEqual(len(updated["selected"]), 2)
        self.assertTrue(updated["categories"]["test"][0]["selected"])


class TestReviewService(unittest.TestCase):
    """Test ReviewService."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'topics': [],
            'canadian_boost': 1.0,
            'max_articles': 8
        }
        self.temp_dir = tempfile.mkdtemp()
        self.service = ReviewService(self.config, Path(self.temp_dir))

    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_get_review_summary_no_review(self):
        """Test getting summary when no review exists."""
        summary = self.service.get_review_summary()

        self.assertFalse(summary['has_review'])
        self.assertEqual(summary['total_articles'], 0)

    def test_clear_review(self):
        """Test clearing review data."""
        # Create a review first
        review_data = {
            "date": "2024-01-01",
            "total_articles": 0,
            "categories": {},
            "selected": []
        }
        self.service.repository.save_review(review_data)

        # Clear it
        success = self.service.clear_review()
        self.assertTrue(success)

        # Verify it's gone
        loaded = self.service.load_review()
        self.assertIsNone(loaded)


if __name__ == '__main__':
    unittest.main()
