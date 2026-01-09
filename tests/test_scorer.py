"""Unit tests for article scoring module."""

import unittest
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sources.rss_fetcher import Article
from processors.scorer import (
    calculate_topic_score,
    calculate_recency_score,
    calculate_priority_score,
    score_articles,
    get_top_articles
)


class TestScoringFunctions(unittest.TestCase):
    """Test individual scoring functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.article_recent = Article(
            title="AI Breakthrough: New Model Achieves AGI Capabilities",
            url="https://example.com/ai-agi",
            source="Tech News",
            published=datetime.now(),
            summary="A new AI model demonstrates AGI-level capabilities",
            category="capabilities"
        )

        self.article_old = Article(
            title="Old AI News",
            url="https://example.com/old-ai",
            source="Tech News",
            published=datetime.now() - timedelta(days=10),
            summary="This is from 10 days ago",
            category="news"
        )

        self.config = {
            'topics': [
                {
                    'name': 'AGI',
                    'keywords': ['AGI', 'artificial general intelligence', 'breakthrough'],
                    'category': 'capabilities',
                    'priority': 2.0
                },
                {
                    'name': 'Governance',
                    'keywords': ['regulation', 'governance', 'policy'],
                    'category': 'governance',
                    'priority': 1.5
                }
            ]
        }

    def test_topic_score_matches_keywords(self):
        """Test that topic score increases for keyword matches."""
        score = calculate_topic_score(self.article_recent, self.config)
        self.assertGreater(score, 0, "Article with matching keywords should have positive score")

    def test_topic_score_no_match(self):
        """Test that articles without matching keywords get score 0."""
        article = Article(
            title="Random article",
            url="https://example.com/random",
            source="News",
            published=datetime.now(),
            summary="No relevant keywords here",
            category="other"
        )
        score = calculate_topic_score(article, self.config)
        self.assertEqual(score, 0, "Article without keywords should have zero topic score")

    def test_recency_score_recent_article(self):
        """Test that recent articles get higher recency scores."""
        score_recent = calculate_recency_score(self.article_recent, days_old=0)
        score_old = calculate_recency_score(self.article_old, days_old=10)
        self.assertGreater(score_recent, score_old, "Recent articles should score higher")

    def test_priority_score_high_priority(self):
        """Test priority score for different priority levels."""
        article_high = Article(
            title="Test",
            url="https://example.com",
            source="Test",
            published=datetime.now(),
            summary="Test",
            priority="high"
        )
        article_low = Article(
            title="Test",
            url="https://example.com",
            source="Test",
            published=datetime.now(),
            summary="Test",
            priority="low"
        )

        score_high = calculate_priority_score(article_high)
        score_low = calculate_priority_score(article_low)
        self.assertGreater(score_high, score_low, "High priority should score higher")


class TestArticleScoring(unittest.TestCase):
    """Test the full article scoring pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.articles = [
            Article(
                title="AI AGI Breakthrough",
                url="https://example.com/1",
                source="Tech News",
                published=datetime.now(),
                summary="New AGI capabilities demonstrated",
                priority="high",
                category="capabilities"
            ),
            Article(
                title="Old News",
                url="https://example.com/2",
                source="Tech News",
                published=datetime.now() - timedelta(days=30),
                summary="Old article from a month ago",
                priority="medium",
                category="news"
            ),
            Article(
                title="Regulation Update",
                url="https://example.com/3",
                source="Policy News",
                published=datetime.now() - timedelta(days=2),
                summary="New AI governance regulation",
                priority="medium",
                category="governance"
            ),
        ]

        self.config = {
            'topics': [
                {
                    'name': 'AGI',
                    'keywords': ['AGI', 'breakthrough'],
                    'category': 'capabilities',
                    'priority': 2.0
                },
                {
                    'name': 'Governance',
                    'keywords': ['regulation', 'governance'],
                    'category': 'governance',
                    'priority': 1.5
                }
            ],
            'canadian_boost': 1.0
        }

    def test_score_articles_returns_all(self):
        """Test that score_articles returns all articles."""
        scored = score_articles(self.articles, self.config)
        self.assertEqual(len(scored), len(self.articles), "All articles should be scored")

    def test_score_articles_have_scores(self):
        """Test that all scored articles have score values."""
        scored = score_articles(self.articles, self.config)
        for article in scored:
            self.assertGreaterEqual(article.score, 0, "All articles should have non-negative score")

    def test_score_articles_ranking(self):
        """Test that articles are ranked correctly."""
        scored = score_articles(self.articles, self.config)
        # Highest scores first
        for i in range(len(scored) - 1):
            self.assertGreaterEqual(
                scored[i].score,
                scored[i+1].score,
                "Articles should be sorted by score descending"
            )

    def test_get_top_articles(self):
        """Test getting top N articles."""
        scored = score_articles(self.articles, self.config)
        top_3 = get_top_articles(scored, 3)
        self.assertLessEqual(len(top_3), 3, "Should return at most 3 articles")

        top_1 = get_top_articles(scored, 1)
        self.assertEqual(len(top_1), 1, "Should return 1 article")
        # Should be the highest scored
        self.assertEqual(top_1[0].url, scored[0].url, "Top article should have highest score")

    def test_get_top_articles_more_than_available(self):
        """Test getting top N articles when N > available articles."""
        scored = score_articles(self.articles, self.config)
        top_100 = get_top_articles(scored, 100)
        self.assertEqual(len(top_100), len(scored), "Should return all articles when N > total")


class TestScorerEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_article_with_no_title(self):
        """Test handling of articles with empty title."""
        article = Article(
            title="",
            url="https://example.com",
            source="Test",
            published=datetime.now(),
            summary="Summary"
        )
        config = {'topics': []}
        # Should not raise an error
        score = calculate_topic_score(article, config)
        self.assertIsNotNone(score)

    def test_article_with_no_summary(self):
        """Test handling of articles with empty summary."""
        article = Article(
            title="Title",
            url="https://example.com",
            source="Test",
            published=datetime.now(),
            summary=""
        )
        config = {'topics': []}
        score = calculate_topic_score(article, config)
        self.assertIsNotNone(score)

    def test_empty_articles_list(self):
        """Test scoring with empty article list."""
        articles = []
        config = {'topics': []}
        scored = score_articles(articles, config)
        self.assertEqual(len(scored), 0)

    def test_config_with_no_topics(self):
        """Test scoring when config has no topics."""
        articles = [
            Article(
                title="Test",
                url="https://example.com",
                source="Test",
                published=datetime.now(),
                summary="Test"
            )
        ]
        config = {'topics': []}
        scored = score_articles(articles, config)
        self.assertEqual(len(scored), 1)
        # Should still have some score (from priority/recency)
        self.assertGreaterEqual(scored[0].score, 0)


if __name__ == '__main__':
    unittest.main()
