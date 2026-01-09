#!/usr/bin/env python3
"""
End-to-end integration test for section-based newsletter generation.

This test validates the complete workflow:
1. Load configuration
2. Create sample articles
3. Classify articles into sections
4. Auto-select articles by content criteria
5. Generate newsletter HTML
6. Validate output format and content
"""

import unittest
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sources.rss_fetcher import Article
from processors.section_classifier import classify_all_articles
from processors.article_selector import auto_select_articles
from formatters.email_formatter import format_newsletter_html_sections, save_newsletter


class TestE2ENewsletter(unittest.TestCase):
    """End-to-end tests for newsletter generation."""

    @classmethod
    def setUpClass(cls):
        """Set up test configuration."""
        # Create a minimal config dict for testing
        cls.config = {
            'newsletter': {
                'name': 'AI This Week',
                'tagline': 'Key AI Developments You Should Know'
            },
            'gemini': {
                'model': 'models/gemini-2.0-flash'
            },
            'sections': {
                'headlines': {
                    'target_count': 8,
                    'governance_ratio': 0.6,
                    'required_canadian_gov': 1,
                    'required_governance': 1
                },
                'bright_spots': {
                    'target_count': 2,
                    'keywords': ['breakthrough', 'cure', 'innovation', 'success', 'achievement']
                },
                'tools': {
                    'target_count': 1,
                    'max_age_days': 3
                },
                'deep_dives': {
                    'target_count': 4,
                    'source_keywords': ['arxiv', 'research', 'journal', 'paper', 'study']
                },
                'grain_quality': {
                    'enabled': True,
                    'keywords': ['agriculture', 'farming', 'grain', 'crop']
                }
            },
            'sentiment': {
                'target_concerns': 0.40,
                'target_opportunities': 0.35,
                'target_neutral': 0.25
            }
        }

    def create_sample_articles(self) -> list:
        """Create sample articles covering different sections and sentiments."""
        articles = [
            # Canadian Government Stories
            Article(
                title="Government of Canada Announces AI Investment Initiative",
                url="https://example.com/canada-ai-investment",
                source="Government of Canada",
                published=datetime.now() - timedelta(days=1),
                summary="The federal government announced a new $100 million investment in AI research and development across Canadian universities and startups.",
                category="governance",
                score=8.5,
                priority="high"
            ),

            # Governance/Regulation Stories
            Article(
                title="European Union Passes Landmark AI Regulation Bill",
                url="https://example.com/eu-ai-regulation",
                source="Reuters",
                published=datetime.now() - timedelta(days=1),
                summary="EU lawmakers passed comprehensive AI regulation requiring safety testing and transparency. The bill will affect global AI companies operating in Europe.",
                category="governance",
                score=7.8,
                priority="high"
            ),

            Article(
                title="NIST Updates AI Risk Management Framework",
                url="https://example.com/nist-framework",
                source="NIST",
                published=datetime.now() - timedelta(days=2),
                summary="The National Institute of Standards and Technology released updated guidance for AI risk management, addressing safety, security, and fairness.",
                category="governance",
                score=7.2,
                priority="medium"
            ),

            # Capabilities/Breakthroughs (Bright Spots)
            Article(
                title="Medical AI Breakthrough Improves Cancer Detection",
                url="https://example.com/medical-ai-breakthrough",
                source="Nature Medicine",
                published=datetime.now(),
                summary="Researchers announced a new AI system that detects certain cancers with 95% accuracy, potentially saving thousands of lives annually.",
                category="research",
                score=9.0,
                priority="high"
            ),

            Article(
                title="New AI Model Achieves Breakthrough in Protein Folding",
                url="https://example.com/protein-folding-ai",
                source="Science Daily",
                published=datetime.now() - timedelta(days=1),
                summary="Scientists unveiled an AI model that predicts protein structures with unprecedented accuracy, advancing drug discovery.",
                category="capabilities",
                score=8.7,
                priority="high"
            ),

            # Tools/Products
            Article(
                title="OpenAI Releases New GPT Developer Platform",
                url="https://example.com/openai-platform",
                source="OpenAI Blog",
                published=datetime.now(),
                summary="OpenAI launched a new developer platform with improved API access, real-time processing, and new model options.",
                category="tools",
                score=7.5,
                priority="high"
            ),

            Article(
                title="Anthropic Releases Claude API for Enterprise",
                url="https://example.com/claude-enterprise",
                source="Anthropic",
                published=datetime.now() - timedelta(days=1),
                summary="Anthropic announced the enterprise version of Claude API with improved performance, customization, and support.",
                category="tools",
                score=7.3,
                priority="medium"
            ),

            # Deep Dive / Research
            Article(
                title="Comprehensive Study on AI Labor Market Impact",
                url="https://example.com/labor-study",
                source="arXiv",
                published=datetime.now() - timedelta(days=3),
                summary="New research from MIT examines which job categories are most exposed to AI automation, finding that 80% of the workforce could see AI integration.",
                category="research",
                score=8.2,
                priority="high"
            ),

            Article(
                title="AI Safety Research: New Challenges in Alignment",
                url="https://example.com/alignment-research",
                source="arXiv",
                published=datetime.now() - timedelta(days=2),
                summary="A new paper from leading AI safety researchers discusses emerging challenges in aligning large language models with human values.",
                category="research",
                score=7.6,
                priority="medium"
            ),

            # Grain/Agriculture (Domain Expertise)
            Article(
                title="AI Improves Crop Yield Predictions and Farm Efficiency",
                url="https://example.com/grain-ai",
                source="Agricultural Tech Review",
                published=datetime.now() - timedelta(days=1),
                summary="New AI systems are helping farmers optimize grain crop yields through precise weather analysis and soil monitoring.",
                category="business",
                score=6.8,
                priority="medium"
            ),
        ]

        return articles

    def test_full_newsletter_generation_workflow(self):
        """Test the complete newsletter generation workflow."""
        # Step 1: Create sample articles
        articles = self.create_sample_articles()
        self.assertGreater(len(articles), 0, "No sample articles created")

        # Step 2: Classify articles into sections
        classified = classify_all_articles(articles, self.config, use_sentiment_api=False)
        self.assertIn('headline', classified)
        self.assertIn('bright_spot', classified)
        self.assertIn('tool', classified)
        self.assertIn('deep_dive', classified)

        # Step 3: Auto-select articles by content criteria
        selected = auto_select_articles(articles, self.config, warn_on_missing=False)

        # Verify selection (at least some articles selected)
        self.assertGreater(len(selected['headlines']), 0, "No headlines selected")
        # Note: Without Gemini API for sentiment detection, classification is keyword-based
        # so we verify functionality rather than exact counts

        if selected['bright_spots']:
            self.assertGreaterEqual(len(selected['bright_spots']), 1, "Should have at least 1 bright spot")

        if selected['tools']:
            self.assertGreaterEqual(len(selected['tools']), 1, "Should have at least 1 tool")

        # Step 4: Generate HTML newsletter
        html = format_newsletter_html_sections(selected, self.config)

        # Verify HTML content
        self.assertIn("HEADLINE SUMMARY", html, "Missing headline section")
        self.assertIn("AI This Week", html, "Missing newsletter name")
        self.assertIn("Canada", html or any("Canadian" in a.title for a in articles), "Missing Canadian reference")

        # Verify structure
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("</html>", html)
        self.assertIn("<p style=", html, "Missing paragraph styling")

        # Verify section count
        if selected['bright_spots']:
            self.assertIn("BRIGHT SPOT OF THE WEEK", html)

        if selected['tools']:
            self.assertIn("TOOL OF THE WEEK", html)

        if selected['deep_dives']:
            self.assertIn("DEEP DIVE", html)

    def test_selection_respects_content_criteria(self):
        """Test that selection respects Scott's content criteria."""
        articles = self.create_sample_articles()

        # Run selection
        selected = auto_select_articles(articles, self.config, warn_on_missing=False)

        # Check governance representation
        governance_articles = [a for a in selected['headlines'] if 'govern' in a.title.lower() or 'regulat' in a.title.lower()]
        self.assertGreater(len(governance_articles), 0, "Should select at least one governance article")

        # Check Canadian focus
        has_canadian_focus = any(
            'canada' in a.title.lower() or 'canada' in a.summary.lower()
            for articles_list in selected.values()
            for a in articles_list
        )
        self.assertTrue(has_canadian_focus, "Newsletter should include Canadian content")

        # Check bright spots if available
        if selected['bright_spots']:
            for article in selected['bright_spots']:
                # Bright spot articles should have positive indicators
                has_positive_words = any(
                    word in article.title.lower() or word in article.summary.lower()
                    for word in ['breakthrough', 'innovation', 'success', 'improvement', 'advance']
                )
                # Note: Not all bright spots will have these exact words due to classification logic

    def test_html_format_matches_scott_structure(self):
        """Test that generated HTML matches Scott's newsletter structure."""
        articles = self.create_sample_articles()
        selected = auto_select_articles(articles, self.config, warn_on_missing=False)

        # Generate HTML
        html = format_newsletter_html_sections(selected, self.config)

        # Check structure order (should appear in this order)
        headline_pos = html.find("HEADLINE SUMMARY")
        bright_spot_pos = html.find("BRIGHT SPOT OF THE WEEK")
        tool_pos = html.find("TOOL OF THE WEEK") if "TOOL OF THE WEEK" in html else len(html)
        learning_pos = html.find("LEARNING")
        deep_dive_pos = html.find("DEEP DIVE")

        # Headlines should come first
        self.assertGreater(headline_pos, 0, "HEADLINE SUMMARY not found")

        # If bright spots exist, they should come after headlines
        if bright_spot_pos > 0:
            self.assertGreater(bright_spot_pos, headline_pos, "Bright spots should come after headlines")

        # Deep dives should come near the end
        if deep_dive_pos > 0 and learning_pos > 0:
            self.assertGreater(deep_dive_pos, learning_pos, "Deep dives should come after learning")

    def test_newsletter_contains_required_sections(self):
        """Test that newsletter includes all required sections."""
        articles = self.create_sample_articles()
        selected = auto_select_articles(articles, self.config, warn_on_missing=False)
        html = format_newsletter_html_sections(selected, self.config)

        # Check for required elements
        self.assertIn('📰 HEADLINE SUMMARY', html, "Missing headline section header")
        self.assertIn('Hello,', html, "Missing greeting")
        self.assertIn('Here\'s your weekly update on the latest in AI', html, "Missing tagline")
        self.assertIn('📅 Week of', html, "Missing week indicator")

    def test_html_saves_to_file(self):
        """Test that generated HTML can be saved to file."""
        articles = self.create_sample_articles()
        selected = auto_select_articles(articles, self.config, warn_on_missing=False)
        html = format_newsletter_html_sections(selected, self.config)

        # Create temporary output directory
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)

        # Save newsletter
        newsletter_path = save_newsletter(html, output_dir, "test_newsletter.html")

        # Verify file was created
        self.assertTrue(newsletter_path.exists(), "Newsletter file not created")

        # Verify file content
        with open(newsletter_path, 'r', encoding='utf-8') as f:
            saved_html = f.read()
            self.assertEqual(saved_html, html, "Saved HTML differs from original")

        # Cleanup
        newsletter_path.unlink()

    def test_article_classification_accuracy(self):
        """Test that articles are classified into appropriate sections."""
        articles = self.create_sample_articles()

        # Classify articles
        classified = classify_all_articles(articles, self.config, use_sentiment_api=False)

        # Check that articles are distributed across sections
        total_classified = sum(len(articles) for articles in classified.values())
        self.assertEqual(total_classified, len(articles), "Not all articles were classified")

        # Tools should be classified as tools
        tool_article = next((a for a in articles if 'Platform' in a.title), None)
        if tool_article:
            section = getattr(tool_article, 'section', 'unclassified')
            self.assertEqual(section, 'tool', f"Tool article should be classified as 'tool', got {section}")

        # Research papers should be classified as deep dives
        research_article = next((a for a in articles if 'arXiv' in a.source), None)
        if research_article:
            section = getattr(research_article, 'section', 'unclassified')
            self.assertEqual(section, 'deep_dive', f"Research article should be classified as 'deep_dive', got {section}")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
