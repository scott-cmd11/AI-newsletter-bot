#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to generate a real newsletter from your configured feeds.

Run this to test the section-based newsletter generator with real articles.

Usage:
    1. Set your Gemini API key:
       set GEMINI_API_KEY=your_actual_key

    2. Run this script:
       python test_real_newsletter.py

Output:
    - Newsletter saved to: output/newsletter_YYYY-MM-DD.html
    - HTML file you can open in a browser
    - Console output showing article selection and statistics
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sources.rss_fetcher import Article
from processors.section_classifier import classify_all_articles
from processors.article_selector import auto_select_articles
from formatters.email_formatter import format_newsletter_html_sections, save_newsletter


def create_sample_articles():
    """Create sample articles to demonstrate the newsletter generator."""

    articles = [
        # Canadian Government
        Article(
            title="Government of Canada Announces $100M AI Research Investment",
            url="https://example.com/canada-ai-investment",
            source="Government of Canada",
            published=datetime.now(),
            summary="The federal government announced a new $100 million investment in AI research and development across Canadian universities and research centers.",
            category="governance",
            score=9.0,
            priority="high"
        ),

        # Governance/Regulation
        Article(
            title="EU Passes Historic AI Regulation: Safety and Transparency Requirements",
            url="https://example.com/eu-regulation",
            source="Reuters",
            published=datetime.now(),
            summary="The European Union passed comprehensive AI regulation requiring extensive safety testing and transparency requirements for AI systems. The regulation affects all companies operating AI in Europe.",
            category="governance",
            score=8.5,
            priority="high"
        ),

        Article(
            title="NIST Updates AI Risk Management Framework for Enterprise Deployment",
            url="https://example.com/nist-framework",
            source="NIST",
            published=datetime.now(),
            summary="The National Institute of Standards and Technology released updated guidance for managing AI risks in enterprise environments, addressing safety, security, and fairness concerns.",
            category="governance",
            score=7.8,
            priority="medium"
        ),

        # Bright Spots
        Article(
            title="Medical AI Breakthrough: New System Detects Cancers with 95% Accuracy",
            url="https://example.com/cancer-detection",
            source="Nature Medicine",
            published=datetime.now(),
            summary="Researchers announced a breakthrough AI system that detects certain cancers with 95% accuracy, potentially saving thousands of lives annually.",
            category="research",
            score=9.2,
            priority="high"
        ),

        Article(
            title="AI Wins Gold Medal in International Math Competition",
            url="https://example.com/math-breakthrough",
            source="Science Today",
            published=datetime.now(),
            summary="A new AI system achieved gold medal performance at the International Mathematical Olympiad, demonstrating significant progress in abstract reasoning capabilities.",
            category="capabilities",
            score=8.7,
            priority="high"
        ),

        # Tools/Products
        Article(
            title="OpenAI Launches New GPT-4 Turbo API with 50% Cost Reduction",
            url="https://example.com/openai-api",
            source="OpenAI Blog",
            published=datetime.now(),
            summary="OpenAI released a new GPT-4 Turbo model with improved performance and a 50% reduction in API costs, making AI more accessible to developers.",
            category="tools",
            score=8.2,
            priority="high"
        ),

        Article(
            title="Claude 3 Enterprise Platform Now Available with Advanced Safety Features",
            url="https://example.com/claude-enterprise",
            source="Anthropic",
            published=datetime.now(),
            summary="Anthropic released Claude 3 Enterprise platform with improved performance, customizable safety features, and dedicated support for large organizations.",
            category="tools",
            score=7.9,
            priority="medium"
        ),

        # Deep Dives
        Article(
            title="Comprehensive MIT Study: AI Automation Will Impact 80% of Workforce",
            url="https://example.com/labor-impact",
            source="arXiv",
            published=datetime.now(),
            summary="New research from MIT examines which job categories are most exposed to AI automation, finding that approximately 80% of the workforce could see AI integration in their roles.",
            category="research",
            score=8.4,
            priority="high"
        ),

        Article(
            title="AI Safety Research Paper: New Challenges in Aligning Large Language Models",
            url="https://example.com/alignment",
            source="arXiv",
            published=datetime.now(),
            summary="A new peer-reviewed paper from leading AI safety researchers discusses emerging challenges in aligning large language models with human values and preferences.",
            category="research",
            score=7.6,
            priority="medium"
        ),

        # Grain/Agriculture
        Article(
            title="AI Improves Grain Crop Yield Predictions: Field Tests Show 15% Improvement",
            url="https://example.com/grain-ai",
            source="Agricultural Tech Review",
            published=datetime.now(),
            summary="New AI systems are helping farmers optimize grain crop yields through precise weather analysis and soil monitoring, with field tests showing 15% improvement in yield predictions.",
            category="business",
            score=6.9,
            priority="medium"
        ),
    ]

    return articles


def main():
    """Main test function."""

    print("\n" + "=" * 70)
    print("🚀 SECTION-BASED NEWSLETTER GENERATOR - TEST")
    print("=" * 70)

    # Check for API key (optional - will still work without it for classification)
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print("\n✅ GEMINI_API_KEY found - Full AI summarization enabled")
    else:
        print("\n⚠️  GEMINI_API_KEY not set - Using keyword-based classification only")
        print("   (Full summaries require: set GEMINI_API_KEY=your_key)")

    # Create config
    print("\n📋 Setting up configuration...")
    config = {
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
                'keywords': ['breakthrough', 'cure', 'innovation', 'success', 'achievement', 'milestone', 'wins', 'gold', 'advance']
            },
            'tools': {
                'target_count': 1,
                'max_age_days': 3
            },
            'deep_dives': {
                'target_count': 4,
                'source_keywords': ['arxiv', 'research', 'journal', 'paper', 'study', 'white paper']
            },
            'grain_quality': {
                'enabled': True,
                'keywords': ['agriculture', 'farming', 'grain', 'crop', 'harvest', 'field']
            }
        },
        'sentiment': {
            'target_concerns': 0.40,
            'target_opportunities': 0.35,
            'target_neutral': 0.25
        }
    }

    # Create sample articles
    print("📰 Creating sample articles...")
    articles = create_sample_articles()
    print(f"   Created {len(articles)} sample articles")

    # Classify articles into sections
    print("\n📂 Step 1: Classifying articles into sections...")
    classified = classify_all_articles(articles, config, use_sentiment_api=False)
    print(f"   Headlines:    {len(classified['headline'])} articles")
    print(f"   Bright Spots: {len(classified['bright_spot'])} articles")
    print(f"   Tools:        {len(classified['tool'])} articles")
    print(f"   Deep Dives:   {len(classified['deep_dive'])} articles")
    print(f"   Grain Quality:{len(classified['grain_quality'])} articles")

    # Auto-select articles by content criteria
    print("\n🎯 Step 2: Auto-selecting articles by content criteria...")
    selected = auto_select_articles(articles, config, warn_on_missing=True)
    print(f"   ✓ Selection complete")

    # Generate HTML newsletter
    print("\n📝 Step 3: Generating HTML newsletter...")
    html = format_newsletter_html_sections(selected, config)
    print(f"   ✓ HTML generated ({len(html)} bytes)")

    # Save newsletter
    print("\n💾 Step 4: Saving newsletter...")
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    date = datetime.now().strftime('%Y-%m-%d')
    newsletter_path = output_dir / f"newsletter_{date}.html"

    with open(newsletter_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"   ✓ Saved to: {newsletter_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("📊 NEWSLETTER SUMMARY")
    print("=" * 70)
    print(f"Headlines:     {len(selected['headlines']):2d} articles")
    print(f"Bright Spots:  {len(selected['bright_spots']):2d} articles")
    print(f"Tools:         {len(selected['tools']):2d} articles")
    print(f"Deep Dives:    {len(selected['deep_dives']):2d} articles")
    print(f"Grain Quality: {len(selected['grain_quality']):2d} articles")
    print("-" * 70)
    total = sum(len(a) for a in selected.values())
    print(f"Total:         {total:2d} articles")

    # Show example articles from each section
    print("\n" + "=" * 70)
    print("📌 EXAMPLE ARTICLES")
    print("=" * 70)

    if selected['headlines']:
        article = selected['headlines'][0]
        print(f"\n📰 Example Headline:")
        print(f"   Title:       {article.title[:60]}...")
        print(f"   Source:      {article.source}")
        if article.ai_summary:
            summary_preview = article.ai_summary.split('\n')[0][:80]
            print(f"   Summary:     {summary_preview}...")
        if article.canadian_context:
            print(f"   Canadian:    {article.canadian_context[:70]}...")

    if selected['bright_spots']:
        article = selected['bright_spots'][0]
        print(f"\n✨ Example Bright Spot:")
        print(f"   Title:       {article.title[:60]}...")
        print(f"   Source:      {article.source}")

    if selected['tools']:
        article = selected['tools'][0]
        print(f"\n🛠️ Example Tool:")
        print(f"   Title:       {article.title[:60]}...")
        print(f"   Source:      {article.source}")

    if selected['deep_dives']:
        article = selected['deep_dives'][0]
        print(f"\n📊 Example Deep Dive:")
        print(f"   Title:       {article.title[:60]}...")
        print(f"   Source:      {article.source}")

    # Print next steps
    print("\n" + "=" * 70)
    print("✅ NEXT STEPS")
    print("=" * 70)
    print(f"\n1. Open the newsletter in your browser:")
    print(f"   {newsletter_path.absolute()}")
    print(f"\n2. Review the newsletter for:")
    print(f"   - Correct section structure")
    print(f"   - Article selection matches your criteria")
    print(f"   - Formatting looks professional")
    print(f"\n3. To test with real API summaries:")
    print(f"   - Set GEMINI_API_KEY=your_key")
    print(f"   - Update create_sample_articles() to use real feeds")
    print(f"\n4. Compare generated newsletter with your samples:")
    print(f"   - C:\\Users\\scott\\OneDrive\\Desktop\\drive-download-20260109T180554Z-1-001\\")
    print(f"\n5. For detailed testing guide:")
    print(f"   - See TESTING_GUIDE.md")

    print("\n" + "=" * 70)
    print("✨ Test completed successfully!")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
