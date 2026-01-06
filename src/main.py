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

import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from sources.rss_fetcher import fetch_all_articles
from processors.scorer import score_articles, get_top_articles, print_article_rankings
from processors.summarizer import summarize_articles, generate_deep_dive_topic
from formatters.email_formatter import format_newsletter_html, save_newsletter


def load_config() -> dict:
    """Load configuration from YAML file."""
    config_path = Path(__file__).parent.parent / "config" / "sources.yaml"
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)
        
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


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
    
    # Load configuration
    config = load_config()
    newsletter_config = config.get('newsletter', {})
    
    print(f"📰 Newsletter: {newsletter_config.get('name', 'AI This Week')}")
    print(f"📬 Google Alerts: {len(config.get('google_alerts', []))} configured")
    print(f"📡 RSS Feeds: {len(config.get('rss_feeds', []))} configured")
    
    # Determine max articles
    max_articles = args.max_articles or newsletter_config.get('max_articles', 8)
    
    # ========================================
    # Step 1: Fetch articles from all sources
    # ========================================
    print("\n" + "=" * 60)
    print("📥 STEP 1: Fetching Articles")
    print("=" * 60)
    
    articles = fetch_all_articles(config)
    
    if not articles:
        print("\n❌ No articles found. Check your source configuration.")
        sys.exit(1)
    
    # ========================================
    # Step 2: Score and rank articles
    # ========================================
    print("\n" + "=" * 60)
    print("📊 STEP 2: Scoring & Ranking")
    print("=" * 60)
    
    scored_articles = score_articles(articles, config)
    top_articles = get_top_articles(scored_articles, max_articles)
    
    print_article_rankings(scored_articles, top_n=15)
    
    # Save to JSON for review
    output_dir = Path(__file__).parent.parent / "output"
    json_file = save_articles_json(scored_articles, output_dir)
    print(f"\n💾 Saved all articles to: {json_file}")
    
    if args.fetch_only:
        print("\n✅ Fetch complete (--fetch-only mode)")
        return
    
    # ========================================
    # Step 3: Generate AI summaries
    # ========================================
    if not args.no_ai:
        print("\n" + "=" * 60)
        print("🤖 STEP 3: AI Summarization")
        print("=" * 60)
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("⚠️  GEMINI_API_KEY not set - using original summaries")
            print("   Set it with: $env:GEMINI_API_KEY='your-key-here'")
        else:
            top_articles = summarize_articles(top_articles, config)
            
            # Generate deep dive suggestion
            deep_dive = generate_deep_dive_topic(top_articles, config)
            print(f"\n💡 Deep Dive Suggestion: {deep_dive.get('topic', 'N/A')}")
    else:
        print("\n⏭️  Skipping AI summarization (--no-ai mode)")
        deep_dive = None
    
    # ========================================
    # Step 4: Format newsletter
    # ========================================
    print("\n" + "=" * 60)
    print("📧 STEP 4: Formatting Newsletter")
    print("=" * 60)
    
    html = format_newsletter_html(
        articles=top_articles,
        config=config,
        deep_dive=deep_dive if not args.no_ai else None
    )
    
    # Save newsletter
    output_file = save_newsletter(html, output_dir)
    print(f"\n✅ Newsletter saved to: {output_file}")
    
    # Open in browser if requested
    if args.preview:
        print("🌐 Opening in browser...")
        webbrowser.open(f'file://{output_file.absolute()}')
    
    print("\n" + "=" * 60)
    print("✅ COMPLETE!")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"  1. Review: {output_file}")
    print(f"  2. Edit articles if needed: {json_file}")
    print(f"  3. Copy HTML into Outlook email")
    print()


if __name__ == "__main__":
    main()
