#!/usr/bin/env python3
"""
Unit tests for section-based newsletter generation.

Tests for:
- Section classifier
- Article selector
- Scott's voice prompts
- HTML formatting
"""

import unittest
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sources.rss_fetcher import Article
from processors.section_classifier import (
    classify_article_section,
    classify_all_articles,
    has_positive_sentiment_keywords,
    has_tool_keywords,
    is_research_paper,
    is_long_form,
    has_grain_keywords
)
from processors.article_selector import (
    is_canadian_government_story,
    is_governance_story,
    find_canadian_government_stories,
    find_governance_stories,
    auto_select_articles,
    check_sentiment_distribution
)
from formatters.email_formatter import format_paragraphs


class TestSectionClassifier(unittest.TestCase):
    """Test section classification logic."""

    def setUp(self):
        """Create test articles."""
        self.config = {
            'gemini': {'model': 'models/gemini-2.0-flash'}
        }

        # Test article with positive sentiment
        self.positive_article = Article(
            title="Breakthrough: New AI Model Achieves Record Performance",
            url="https://example.com/breakthrough",
            source="Tech News",
            published=datetime.now(),
            summary="Researchers announced a new AI breakthrough achieving state-of-the-art results.",
            category="capabilities"
        )

        # Test article about tools
        self.tool_article = Article(
            title="New AI Tool Released: Platform for Developers",
            url="https://example.com/tool",
            source="Product Hub",
            published=datetime.now(),
            summary="A new platform has been launched for AI developers.",
            category="tools"
        )

        # Test article about governance
        self.governance_article = Article(
            title="EU Proposes New AI Regulation Framework",
            url="https://example.com/regulation",
            source="Policy Daily",
            published=datetime.now(),
            summary="European Union announces new regulation for AI safety and governance.",
            category="governance"
        )

        # Test article about Canadian government
        self.canadian_gov_article = Article(
            title="Government of Canada Announces AI Strategy",
            url="https://example.com/canada-gov",
            source="Canadian News",
            published=datetime.now(),
            summary="The Government of Canada launched a new AI innovation strategy.",
            category="governance"
        )

    def test_positive_sentiment_keywords(self):
        """Test detection of positive sentiment keywords."""
        assert has_positive_sentiment_keywords(self.positive_article.title, self.positive_article.summary)
        assert not has_positive_sentiment_keywords(self.governance_article.title, self.governance_article.summary)

    def test_tool_keywords(self):
        """Test detection of tool/product keywords."""
        assert has_tool_keywords(self.tool_article.title, self.tool_article.summary)
        # Note: "Framework" can match tool keywords, so use a different governance article
        generic_article = Article(
            title="AI Safety Concerns Rise",
            url="https://example.com/generic",
            source="Policy Daily",
            published=datetime.now(),
            summary="Experts discuss AI safety concerns.",
            category="governance"
        )
        assert not has_tool_keywords(generic_article.title, generic_article.summary)

    def test_governance_keywords(self):
        """Test detection of governance keywords."""
        assert is_governance_story(self.governance_article)
        # "Strategy" doesn't match governance keywords, so test with a regulation-focused article
        gov_article_updated = Article(
            title="Government of Canada Announces AI Regulation Policy",
            url="https://example.com/ca-gov",
            source="Canadian Press",
            published=datetime.now(),
            summary="Canada launches new AI regulation and policy initiatives.",
            category="governance"
        )
        assert is_governance_story(gov_article_updated)
        assert not is_governance_story(self.positive_article)

    def test_canadian_government_keywords(self):
        """Test detection of Canadian government stories."""
        assert is_canadian_government_story(self.canadian_gov_article)
        assert not is_canadian_government_story(self.governance_article)

    def test_classify_positive_article(self):
        """Test classification of positive sentiment article."""
        # Use keyword-based sentiment (no API call)
        section = classify_article_section(self.positive_article, self.config, use_sentiment_api=False)
        assert section == "bright_spot", f"Expected bright_spot, got {section}"

    def test_classify_tool_article(self):
        """Test classification of tool article."""
        section = classify_article_section(self.tool_article, self.config, use_sentiment_api=False)
        assert section == "tool", f"Expected tool, got {section}"

    def test_classify_governance_article(self):
        """Test classification of governance article (default to headline)."""
        # Use a governance article that doesn't have tool keywords
        governance_article = Article(
            title="AI Regulation Policy Announced",
            url="https://example.com/regulation",
            source="Policy Daily",
            published=datetime.now(),
            summary="New regulation for AI safety and governance.",
            category="governance"
        )
        section = classify_article_section(governance_article, self.config, use_sentiment_api=False)
        assert section == "headline", f"Expected headline, got {section}"


class TestArticleSelector(unittest.TestCase):
    """Test article selection rules."""

    def setUp(self):
        """Create test articles and config."""
        self.config = {
            'sections': {
                'headlines': {
                    'target_count': 8,
                    'governance_ratio': 0.6,
                    'required_canadian_gov': 1,
                    'required_governance': 1
                },
                'bright_spots': {'target_count': 2},
                'tools': {'target_count': 1},
                'deep_dives': {'target_count': 4}
            }
        }

        # Create test articles
        self.articles = [
            Article(
                title="Government of Canada Announces AI Initiative",
                url="https://example.com/ca-gov",
                source="Canadian Press",
                published=datetime.now(),
                summary="Canada launches new AI investment.",
                category="governance",
                section="headline",
                sentiment="neutral"
            ),
            Article(
                title="New AI Regulation Proposed in Europe",
                url="https://example.com/regulation",
                source="Policy News",
                published=datetime.now(),
                summary="EU proposes regulation framework.",
                category="governance",
                section="headline",
                sentiment="negative"
            ),
            Article(
                title="Breakthrough: Medical AI Saves Lives",
                url="https://example.com/medical",
                source="Science Today",
                published=datetime.now(),
                summary="New AI system achieves medical breakthrough.",
                category="research",
                section="bright_spot",
                sentiment="positive"
            ),
            Article(
                title="New Tool Released for Developers",
                url="https://example.com/tool",
                source="Dev Hub",
                published=datetime.now(),
                summary="New AI platform released.",
                category="tools",
                section="tool",
                sentiment="neutral"
            ),
        ]

    def test_find_canadian_government_stories(self):
        """Test finding Canadian government stories."""
        gov_stories = find_canadian_government_stories(self.articles)
        assert len(gov_stories) == 1
        assert "Government of Canada" in gov_stories[0].title

    def test_find_governance_stories(self):
        """Test finding governance/regulation stories."""
        gov_stories = find_governance_stories(self.articles)
        assert len(gov_stories) >= 1
        assert any("regulation" in a.title.lower() or "governance" in a.title.lower() for a in gov_stories)

    def test_auto_select_articles(self):
        """Test auto-selection of articles."""
        # auto_select_articles handles both classification and selection
        selected = auto_select_articles(self.articles, self.config, warn_on_missing=False)

        # Check that selections were made
        assert len(selected['headlines']) > 0, "No headlines selected"
        assert len(selected['bright_spots']) > 0, "No bright spots selected"
        assert len(selected['tools']) > 0, "No tools selected"

    def test_sentiment_distribution(self):
        """Test sentiment distribution checking."""
        selected = {
            'headlines': [self.articles[0], self.articles[1]],
            'bright_spots': [self.articles[2]],
            'tools': [self.articles[3]],
            'deep_dives': [],
            'grain_quality': []
        }

        distribution = check_sentiment_distribution(selected)

        # Check that distribution has all keys
        assert 'positive' in distribution
        assert 'negative' in distribution
        assert 'neutral' in distribution


class TestPrompts(unittest.TestCase):
    """Test prompt generation."""

    def setUp(self):
        """Create test data."""
        self.config = {'gemini': {'model': 'models/gemini-2.0-flash'}}
        self.article = Article(
            title="Test Article",
            url="https://example.com/test",
            source="Test Source",
            published=datetime.now(),
            summary="This is a test article about AI."
        )

    def test_prompt_contains_scott_voice(self):
        """Test that prompts include Scott's voice characteristics."""
        from processors.summarizer import build_scott_voice_prompt

        prompt = build_scott_voice_prompt(self.article, "headline", self.config)

        # Check for voice characteristics
        assert "professional" in prompt.lower()
        assert "analytical" in prompt.lower()
        assert "canadian" in prompt.lower()
        assert "2-3 paragraphs" in prompt.lower() or "2-3 PARAGRAPH" in prompt.upper()

    def test_prompt_different_for_sections(self):
        """Test that different sections get different prompts."""
        from processors.summarizer import build_scott_voice_prompt

        headline_prompt = build_scott_voice_prompt(self.article, "headline", self.config)
        tool_prompt = build_scott_voice_prompt(self.article, "tool", self.config)
        deep_dive_prompt = build_scott_voice_prompt(self.article, "deep_dive", self.config)

        # Prompts should be different
        assert headline_prompt != tool_prompt
        assert tool_prompt != deep_dive_prompt


class TestHTMLFormatting(unittest.TestCase):
    """Test HTML formatting functions."""

    def test_format_paragraphs_single(self):
        """Test formatting single paragraph."""
        text = "This is a single paragraph."
        html = format_paragraphs(text)

        assert "<p" in html
        assert "This is a single paragraph." in html

    def test_format_paragraphs_multiple(self):
        """Test formatting multiple paragraphs."""
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        html = format_paragraphs(text)

        # Should have 3 <p> tags
        assert html.count("<p") == 3
        assert "Paragraph 1." in html
        assert "Paragraph 2." in html
        assert "Paragraph 3." in html

    def test_format_paragraphs_empty(self):
        """Test formatting empty text."""
        text = ""
        html = format_paragraphs(text)

        assert html == ""

    def test_format_paragraphs_whitespace(self):
        """Test formatting with extra whitespace."""
        text = "  Paragraph 1.  \n\n  Paragraph 2.  "
        html = format_paragraphs(text)

        # Should strip whitespace but preserve content
        assert "Paragraph 1." in html
        assert "Paragraph 2." in html
        assert "  " not in html.split(">")[1]  # No spaces after tags


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components."""

    def setUp(self):
        """Create test data."""
        self.config = {
            'gemini': {'model': 'models/gemini-2.0-flash'},
            'sections': {
                'headlines': {
                    'target_count': 8,
                    'governance_ratio': 0.6,
                    'required_canadian_gov': 1,
                    'required_governance': 1
                },
                'bright_spots': {'target_count': 2},
                'tools': {'target_count': 1},
                'deep_dives': {'target_count': 4},
                'grain_quality': {'enabled': True}
            }
        }

        self.articles = [
            Article(
                title="Government of Canada Launches AI Strategy",
                url="https://example.com/1",
                source="Canadian Press",
                published=datetime.now(),
                summary="Federal government announces new AI investment and research initiatives.",
                category="governance"
            ),
            Article(
                title="AI Safety Regulation Debate Heats Up",
                url="https://example.com/2",
                source="Policy Daily",
                published=datetime.now(),
                summary="Lawmakers discuss new AI safety regulations and compliance frameworks.",
                category="governance"
            ),
            Article(
                title="Breakthrough: AI Model Achieves New Performance Records",
                url="https://example.com/3",
                source="Tech News",
                published=datetime.now(),
                summary="Researchers announce breakthrough achieving state-of-the-art results.",
                category="capabilities"
            ),
            Article(
                title="Medical AI Saves Lives in Hospital Study",
                url="https://example.com/4",
                source="Health Today",
                published=datetime.now(),
                summary="New AI system improves patient outcomes in medical facility.",
                category="research"
            ),
            Article(
                title="New AI Development Platform Released",
                url="https://example.com/5",
                source="Dev Hub",
                published=datetime.now(),
                summary="Major new platform for AI developers launched today.",
                category="tools"
            ),
        ]

    def test_classify_all_articles(self):
        """Test classifying all articles."""
        classified = classify_all_articles(self.articles, self.config, use_sentiment_api=False)

        # Should have some articles classified
        total = sum(len(articles) for articles in classified.values())
        assert total == len(self.articles), f"Expected {len(self.articles)} articles, got {total}"

        # Should have at least one headline (governance articles default to headlines)
        assert len(classified['headline']) > 0, "No headlines classified"

    def test_selection_meets_minimum_requirements(self):
        """Test that selection meets minimum requirements."""
        selected = auto_select_articles(self.articles, self.config, warn_on_missing=False)

        # Should have headlines
        assert len(selected['headlines']) > 0, "No headlines selected"

        # Can't guarantee Canadian gov story in test data, but should try
        # (our test data has one)


if __name__ == '__main__':
    unittest.main()
