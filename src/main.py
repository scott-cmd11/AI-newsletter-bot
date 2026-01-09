#!/usr/bin/env python3
"""
AI Newsletter Bot - Main Entry Point

This script orchestrates the newsletter generation process:
1. Fetch articles from configured sources (Google Alerts, RSS)
2. Score and rank articles by relevance (Canadian boost, topics)
3. Generate AI summaries using Gemini
4. Format into Outlook-ready HTML email

Usage:
    python src/main.py                    # Full pipeline
    python src/main.py --fetch-only       # Only fetch and score
    python src/main.py --no-ai            # Skip AI summarization
    python src/main.py --preview          # Open in browser when done
"""

import os
import sys
import argparse
import json
import webbrowser
from datetime import datetime
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config.loader import load_config, ConfigError
from logger import setup_logger
from sources.rss_fetcher import fetch_all_articles
from processors.scorer import score_articles, get_top_articles, print_article_rankings
from processors.summarizer import summarize_articles, generate_deep_dive_topic
from formatters.email_formatter import format_newsletter_html, save_newsletter

logger = setup_logger("main")


def save_articles_json(articles, output_dir: Path):
    """Save articles to JSON for review/editing."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"articles_{datetime.now().strftime('%Y-%m-%d')}.json"
    
    data = [a.to_dict() for a in articles]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
        
    return output_file


def main():
    """Main entry point for the newsletter bot."""
    parser = argparse.ArgumentParser(description='AI Newsletter Bot')
    parser.add_argument('--fetch-only', action='store_true', 
                        help='Only fetch and score articles, no summarization')
    parser.add_argument('--no-ai', action='store_true',
                        help='Skip AI summarization')
    parser.add_argument('--preview', action='store_true',
                        help='Open newsletter in browser when done')
    parser.add_argument('--max-articles', type=int, default=None,
                        help='Override max articles from config')
    
    args = parser.parse_args()

    print("=" * 60)
    print("🤖 AI Newsletter Bot")
    print("=" * 60)
    print(f"📅 Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    logger.info("Starting newsletter bot")

    # Load configuration
    try:
        config = load_config()
        logger.info("Configuration loaded successfully")
    except ConfigError as e:
        print(f"❌ Configuration error: {e}")
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    newsletter_config = config.get('newsletter', {})

    print(f"📰 Newsletter: {newsletter_config.get('name', 'AI This Week')}")
    print(f"📬 Google Alerts: {len(config.get('google_alerts', []))} configured")
    print(f"📡 RSS Feeds: {len(config.get('rss_feeds', []))} configured")
    logger.info(f"Configuration: {len(config.get('google_alerts', []))} Google Alerts, {len(config.get('rss_feeds', []))} RSS feeds")
    
    # Determine max articles
    max_articles = args.max_articles or newsletter_config.get('max_articles', 8)
    
    # ========================================
    # Step 1: Fetch articles from all sources
    # ========================================
    print("\n" + "=" * 60)
    print("📥 STEP 1: Fetching Articles")
    print("=" * 60)

    logger.info("Starting article fetch")
    articles = fetch_all_articles(config)

    if not articles:
        print("\n❌ No articles found. Check your source configuration.")
        logger.error("No articles found after fetching from all sources")
        sys.exit(1)

    logger.info(f"Fetched {len(articles)} articles from all sources")
    
    # ========================================
    # Step 2: Score and rank articles
    # ========================================
    print("\n" + "=" * 60)
    print("📊 STEP 2: Scoring & Ranking")
    print("=" * 60)

    logger.info(f"Scoring {len(articles)} articles")
    scored_articles = score_articles(articles, config)
    top_articles = get_top_articles(scored_articles, max_articles)
    logger.info(f"Selected top {len(top_articles)} articles out of {len(scored_articles)}")

    print_article_rankings(scored_articles, top_n=15)

    # Save to JSON for review
    output_dir = Path(__file__).parent.parent / "output"
    json_file = save_articles_json(scored_articles, output_dir)
    print(f"\n💾 Saved all articles to: {json_file}")
    logger.info(f"Saved articles to {json_file}")
    
    if args.fetch_only:
        print("\n✅ Fetch complete (--fetch-only mode)")
        logger.info("Exiting early due to --fetch-only flag")
        return

    # ========================================
    # Step 3: Generate AI summaries
    # ========================================
    if not args.no_ai:
        print("\n" + "=" * 60)
        print("🤖 STEP 3: AI Summarization")
        print("=" * 60)

        logger.info("Starting AI summarization")
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("⚠️  GEMINI_API_KEY not set - using original summaries")
            print("   Set it with: $env:GEMINI_API_KEY='your-key-here'")
            logger.warning("GEMINI_API_KEY not set - using original summaries")
        else:
            logger.info(f"Summarizing {len(top_articles)} articles with Gemini")
            top_articles = summarize_articles(top_articles, config)

            # Generate deep dive suggestion
            logger.info("Generating deep dive topic suggestion")
            deep_dive = generate_deep_dive_topic(top_articles, config)
            print(f"\n💡 Deep Dive Suggestion: {deep_dive.get('topic', 'N/A')}")
    else:
        print("\n⏭️  Skipping AI summarization (--no-ai mode)")
        logger.info("Skipping AI summarization due to --no-ai flag")
        deep_dive = None
    
    # ========================================
    # Step 4: Format newsletter
    # ========================================
    print("\n" + "=" * 60)
    print("📧 STEP 4: Formatting Newsletter")
    print("=" * 60)

    logger.info("Formatting newsletter HTML")
    html = format_newsletter_html(
        articles=top_articles,
        config=config,
        deep_dive=deep_dive if not args.no_ai else None
    )

    # Save newsletter
    output_file = save_newsletter(html, output_dir)
    print(f"\n✅ Newsletter saved to: {output_file}")
    logger.info(f"Newsletter saved to {output_file}")

    # Open in browser if requested
    if args.preview:
        print("🌐 Opening in browser...")
        logger.info("Opening newsletter in browser")
        webbrowser.open(f'file://{output_file.absolute()}')

    print("\n" + "=" * 60)
    print("✅ COMPLETE!")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"  1. Review: {output_file}")
    print(f"  2. Edit articles if needed: {json_file}")
    print(f"  3. Copy HTML into Outlook email")
    print()
    logger.info("Newsletter generation complete")


if __name__ == "__main__":
    main()
