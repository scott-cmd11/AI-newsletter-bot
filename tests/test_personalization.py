"""Unit tests for PersonalizationService."""

import unittest
import tempfile
import json
from datetime import datetime
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.personalization_service import PersonalizationService, PreferenceProfile


class TestPreferenceProfile(unittest.TestCase):
    """Test PreferenceProfile."""

    def test_create_preference_profile(self):
        """Test creating an empty preference profile."""
        profile = PreferenceProfile()

        self.assertEqual(profile.total_selections, 0)
        self.assertEqual(profile.total_available, 0)
        self.assertEqual(profile.selection_rate, 0.0)
        self.assertEqual(len(profile.source_preferences), 0)
        self.assertEqual(len(profile.category_preferences), 0)

    def test_preference_profile_to_dict(self):
        """Test converting preference profile to dictionary."""
        profile = PreferenceProfile()
        profile.total_selections = 10
        profile.total_available = 100
        profile.source_preferences = {"source1": 1.5}

        profile_dict = profile.to_dict()

        self.assertEqual(profile_dict["total_selections"], 10)
        self.assertEqual(profile_dict["total_available"], 100)
        self.assertIn("source1", profile_dict["source_preferences"])


class TestPersonalizationService(unittest.TestCase):
    """Test PersonalizationService."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = PersonalizationService(Path(self.temp_dir))

    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_initialize_personalization_service(self):
        """Test service initialization."""
        self.assertIsNotNone(self.service)
        # preferred_sources is initialized as empty list, not None
        self.assertEqual(len(self.service.preference_profile.preferred_sources), 0)

    def _create_review_file(self, date: str, articles: list, selected: list) -> None:
        """Helper to create a review file."""
        categories = {}
        for article in articles:
            category = article.get('category', 'uncategorized')
            if category not in categories:
                categories[category] = []
            categories[category].append(article)

        review_data = {
            "date": date,
            "total_articles": len(articles),
            "categories": categories,
            "selected": selected
        }

        review_file = Path(self.temp_dir) / f"review_{date}.json"
        with open(review_file, 'w', encoding='utf-8') as f:
            json.dump(review_data, f)

    def test_analyze_historical_selections_no_files(self):
        """Test analyzing with no review files."""
        profile = self.service.analyze_historical_selections()

        self.assertEqual(profile.total_selections, 0)
        self.assertEqual(profile.total_available, 0)

    def test_analyze_historical_selections_single_file(self):
        """Test analyzing with a single review file."""
        articles = [
            {"id": 0, "title": "Article 1", "source": "Source A", "category": "tech", "score": 8.0},
            {"id": 1, "title": "Article 2", "source": "Source B", "category": "tech", "score": 6.0},
        ]
        selected = [
            {"id": 0, "title": "Article 1", "source": "Source A", "category": "tech", "score": 8.0},
        ]

        self._create_review_file("2024-01-01", articles, selected)
        profile = self.service.analyze_historical_selections()

        self.assertEqual(profile.total_selections, 1)
        self.assertEqual(profile.total_available, 2)
        self.assertEqual(profile.selection_rate, 0.5)
        self.assertIn("Source A", profile.source_preferences)

    def test_analyze_multiple_sources(self):
        """Test analyzing selections from multiple sources."""
        articles = [
            {"id": 0, "title": "Article 1", "source": "Source A", "category": "tech", "score": 8.0},
            {"id": 1, "title": "Article 2", "source": "Source B", "category": "tech", "score": 7.0},
            {"id": 2, "title": "Article 3", "source": "Source C", "category": "tech", "score": 6.0},
        ]
        selected = [
            {"id": 0, "title": "Article 1", "source": "Source A", "category": "tech", "score": 8.0},
            {"id": 1, "title": "Article 2", "source": "Source B", "category": "tech", "score": 7.0},
        ]

        self._create_review_file("2024-01-01", articles, selected)
        profile = self.service.analyze_historical_selections()

        # Both sources should have boost multipliers
        self.assertIn("Source A", profile.source_preferences)
        self.assertIn("Source B", profile.source_preferences)

    def test_analyze_categories(self):
        """Test analyzing selections by category."""
        articles = [
            {"id": 0, "title": "Article 1", "source": "Source A", "category": "governance", "score": 8.0},
            {"id": 1, "title": "Article 2", "source": "Source B", "category": "security", "score": 7.0},
            {"id": 2, "title": "Article 3", "source": "Source C", "category": "tools", "score": 6.0},
        ]
        selected = [
            {"id": 0, "title": "Article 1", "source": "Source A", "category": "governance", "score": 8.0},
            {"id": 1, "title": "Article 2", "source": "Source B", "category": "security", "score": 7.0},
        ]

        self._create_review_file("2024-01-01", articles, selected)
        profile = self.service.analyze_historical_selections()

        self.assertIn("governance", profile.category_preferences)
        self.assertIn("security", profile.category_preferences)
        self.assertNotIn("tools", profile.category_preferences)

    def test_boost_article_score_with_source_preference(self):
        """Test score boosting based on source preference."""
        # Set up profile with source preference
        self.service.preference_profile.source_preferences = {"Favorite Source": 1.5}

        article = {
            "title": "Test Article",
            "source": "Favorite Source",
            "category": "tech",
            "score": 5.0
        }

        boosted = self.service.boost_article_score(article)

        # Should get a boost from the preferred source
        self.assertGreater(boosted, article["score"])

    def test_boost_article_score_with_category_preference(self):
        """Test score boosting based on category preference."""
        self.service.preference_profile.category_preferences = {"favorite": 1.5}

        article = {
            "title": "Test Article",
            "source": "Unknown",
            "category": "favorite",
            "score": 5.0
        }

        boosted = self.service.boost_article_score(article)

        self.assertGreater(boosted, article["score"])

    def test_boost_article_score_with_keywords(self):
        """Test score boosting based on keyword matching."""
        self.service.preference_profile.keyword_preferences = {"canada": 5, "artificial": 3}

        article = {
            "title": "Canadian artificial intelligence research",
            "source": "Unknown",
            "category": "tech",
            "score": 5.0
        }

        boosted = self.service.boost_article_score(article)

        # Should boost for keywords
        self.assertGreater(boosted, article["score"])

    def test_predict_selection_likelihood_high(self):
        """Test prediction likelihood for article matching preferences."""
        # Build a profile from historical data with clear preferences
        articles = [
            {"id": 0, "title": "Article 1", "source": "Favorite Source", "category": "tech", "score": 8.5},
            {"id": 1, "title": "Article 2", "source": "Other Source", "category": "tech", "score": 4.0},
            {"id": 2, "title": "Article 3", "source": "Favorite Source", "category": "tech", "score": 7.5},
        ]
        selected = [
            {"id": 0, "title": "Article 1", "source": "Favorite Source", "category": "tech", "score": 8.5},
            {"id": 2, "title": "Article 3", "source": "Favorite Source", "category": "tech", "score": 7.5},
        ]
        self._create_review_file("2024-01-01", articles, selected)
        self.service.analyze_historical_selections()

        # Test prediction for an article matching the preference
        article = {
            "title": "Test Article",
            "source": "Favorite Source",
            "category": "tech",
            "score": 8.0
        }

        likelihood = self.service.predict_selection_likelihood(article)

        # Should be reasonable likelihood given source and score preferences
        self.assertGreaterEqual(likelihood, 35)

    def test_predict_selection_likelihood_low(self):
        """Test prediction likelihood for article not matching preferences."""
        self.service.preference_profile.score_threshold = 7.0
        self.service.preference_profile.score_range = (7.0, 10.0)
        self.service.preference_profile.total_selections = 10
        self.service.preference_profile.preferred_sources = ["Favorite Source"]

        article = {
            "title": "Test Article",
            "source": "Unknown Source",
            "category": "tech",
            "score": 3.0
        }

        likelihood = self.service.predict_selection_likelihood(article)

        # Should be low likelihood
        self.assertLess(likelihood, 50)

    def test_predict_selection_likelihood_range(self):
        """Test that prediction likelihood is always in 0-100 range."""
        self.service.preference_profile.total_selections = 10

        test_articles = [
            {"title": "Great", "source": "A", "category": "tech", "score": 10.0},
            {"title": "Average", "source": "B", "category": "tech", "score": 5.0},
            {"title": "Bad", "source": "C", "category": "tech", "score": 0.0},
        ]

        for article in test_articles:
            likelihood = self.service.predict_selection_likelihood(article)
            self.assertGreaterEqual(likelihood, 0)
            self.assertLessEqual(likelihood, 100)

    def test_get_recommended_articles(self):
        """Test getting recommended articles."""
        self.service.preference_profile.total_selections = 10
        self.service.preference_profile.score_range = (5.0, 10.0)
        self.service.preference_profile.preferred_sources = ["Good Source"]

        articles = [
            {"title": "Article 1", "source": "Good Source", "category": "tech", "score": 8.0},
            {"title": "Article 2", "source": "Other Source", "category": "tech", "score": 7.0},
            {"title": "Article 3", "source": "Good Source", "category": "tech", "score": 6.0},
        ]

        recommendations = self.service.get_recommended_articles(articles, count=2)

        self.assertEqual(len(recommendations), 2)
        # First recommendation should have predicted_likelihood
        self.assertIn("predicted_likelihood", recommendations[0])
        self.assertIn("boosted_score", recommendations[0])

    def test_get_auto_suggestions(self):
        """Test getting auto-suggested articles."""
        self.service.preference_profile.total_selections = 10
        self.service.preference_profile.score_range = (7.0, 10.0)
        self.service.preference_profile.preferred_sources = ["Excellent Source"]

        articles = [
            {"title": "Very Good Article", "source": "Excellent Source", "category": "tech", "score": 9.0},
            {"title": "Good Article", "source": "Other Source", "category": "tech", "score": 6.0},
        ]

        suggestions = self.service.get_auto_suggestions(articles, threshold=75)

        # Only high-confidence suggestions should be returned
        self.assertTrue(all(s["predicted_likelihood"] >= 75 for s in suggestions))

    def test_preference_profile_summary(self):
        """Test getting preference profile summary."""
        self.service.preference_profile.total_selections = 10
        self.service.preference_profile.total_available = 100
        self.service.preference_profile.selection_rate = 0.1
        self.service.preference_profile.score_threshold = 7.0
        self.service.preference_profile.preferred_sources = ["Source A", "Source B"]
        self.service.preference_profile.preferred_categories = ["tech", "governance"]

        summary = self.service.get_preference_profile_summary()

        self.assertIn("10/100", summary)
        self.assertIn("Source A", summary)
        self.assertIn("tech", summary)

    def test_extract_keywords(self):
        """Test keyword extraction."""
        text = "This is artificial intelligence research about Canada"
        keywords = self.service._extract_keywords(text)

        # Should extract significant words
        self.assertTrue(any(k in text.lower() for k in keywords))

    def test_multiple_review_files(self):
        """Test analyzing multiple review files."""
        # Create two review files with different selections
        articles1 = [
            {"id": 0, "title": "Article 1", "source": "Source A", "category": "tech", "score": 8.0},
            {"id": 1, "title": "Article 2", "source": "Source B", "category": "tech", "score": 6.0},
        ]
        selected1 = [{"id": 0, "title": "Article 1", "source": "Source A", "category": "tech", "score": 8.0}]

        articles2 = [
            {"id": 0, "title": "Article 3", "source": "Source A", "category": "governance", "score": 9.0},
            {"id": 1, "title": "Article 4", "source": "Source C", "category": "governance", "score": 5.0},
        ]
        selected2 = [{"id": 0, "title": "Article 3", "source": "Source A", "category": "governance", "score": 9.0}]

        self._create_review_file("2024-01-01", articles1, selected1)
        self._create_review_file("2024-01-02", articles2, selected2)

        profile = self.service.analyze_historical_selections()

        # Should analyze both files
        self.assertEqual(profile.total_selections, 2)
        self.assertEqual(profile.total_available, 4)
        # Source A should be in preferences
        self.assertIn("Source A", profile.source_preferences)


if __name__ == '__main__':
    unittest.main()
