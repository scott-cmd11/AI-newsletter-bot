#!/usr/bin/env python3
"""
Article Curation CLI

A two-step workflow:
1. SCOUT: Fetch and score articles, save for review
2. CURATE: Review articles by category, select ones to include
3. COMPOSE: Generate newsletter from selected articles
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config.loader import load_config, ConfigError
from sources.rss_fetcher import fetch_all_articles
from processors.scorer import score_articles, get_top_articles
from processors.summarizer import summarize_articles
from formatters.email_formatter import format_newsletter_html, save_newsletter


def get_output_dir() -> Path:
    """Get the output directory."""
    return Path(__file__).parent.parent / "output"


def get_today_str() -> str:
    """Get today's date string."""
    return datetime.now().strftime('%Y-%m-%d')


# =============================================================================
# STEP 1: SCOUT - Fetch and score articles
# =============================================================================

def cmd_scout(args):
    """Fetch articles, score them, and save for review."""
    print("=" * 60)
    print("🔍 SCOUT: Fetching and Scoring Articles")
    print("=" * 60)

    try:
        config = load_config()
    except ConfigError as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Fetch articles
    print("\n📥 Fetching from all sources...")
    articles = fetch_all_articles(config)
    
    if not articles:
        print("❌ No articles found!")
        return
    
    # Score articles
    print("\n📊 Scoring and ranking articles...")
    scored = score_articles(articles, config)
    
    # Group by category
    categories = {}
    for article in scored:
        cat = article.category or "uncategorized"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(article)
    
    # Save for review
    output_dir = get_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    review_file = output_dir / f"review_{get_today_str()}.json"
    
    review_data = {
        "date": get_today_str(),
        "total_articles": len(scored),
        "categories": {},
        "selected": []  # Will be populated during curation
    }
    
    for cat, articles_list in categories.items():
        review_data["categories"][cat] = [
            {
                "id": i,
                "title": a.title,
                "url": a.url,
                "source": a.source,
                "score": a.score,
                "summary": a.summary[:200] + "..." if len(a.summary) > 200 else a.summary,
                "published": a.published.isoformat() if a.published else None,
                "selected": False
            }
            for i, a in enumerate(articles_list)
        ]
    
    with open(review_file, 'w', encoding='utf-8') as f:
        json.dump(review_data, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 ARTICLES BY CATEGORY")
    print("=" * 60)
    
    for cat in sorted(categories.keys()):
        articles_list = categories[cat]
        print(f"\n📂 {cat.upper()} ({len(articles_list)} articles)")
        print("-" * 50)
        
        for i, article in enumerate(articles_list[:5]):  # Show top 5 per category
            score_bar = "█" * int(article.score) + "░" * (10 - int(article.score))
            print(f"  [{article.score:5.2f}] {score_bar} {article.title[:50]}")
        
        if len(articles_list) > 5:
            print(f"  ... and {len(articles_list) - 5} more")
    
    print("\n" + "=" * 60)
    print(f"✅ Saved {len(scored)} articles for review")
    print(f"📄 Review file: {review_file}")
    print("=" * 60)
    print("\nNext: Run 'python src/cli.py curate' to select articles")


# =============================================================================
# STEP 2: CURATE - Interactive article selection
# =============================================================================

def cmd_curate(args):
    """Interactive article curation by category."""
    output_dir = get_output_dir()
    review_file = output_dir / f"review_{get_today_str()}.json"
    
    if not review_file.exists():
        print("❌ No review file found. Run 'scout' first.")
        return
    
    with open(review_file, 'r', encoding='utf-8') as f:
        review_data = json.load(f)
    
    print("=" * 60)
    print("✨ CURATE: Select Articles for Newsletter")
    print("=" * 60)
    print("\nFor each category, enter the numbers of articles to include.")
    print("Separate multiple selections with commas (e.g., 1,3,5)")
    print("Press Enter to skip a category.\n")
    
    selected_articles = []
    
    for cat in sorted(review_data["categories"].keys()):
        articles = review_data["categories"][cat]
        
        if not articles:
            continue
            
        print("\n" + "=" * 60)
        print(f"📂 {cat.upper()}")
        print("=" * 60)
        
        for i, article in enumerate(articles, 1):
            score_bar = "█" * int(article["score"]) + "░" * (10 - int(article["score"]))
            print(f"\n  {i}. [{article['score']:5.2f}] {score_bar}")
            print(f"     {article['title'][:70]}")
            print(f"     📰 {article['source']}")
            print(f"     🔗 {article['url'][:60]}...")
        
        print()
        selection = input(f"Select articles for {cat} (e.g., 1,2,3) or Enter to skip: ").strip()
        
        if selection:
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(",")]
                for idx in indices:
                    if 0 <= idx < len(articles):
                        articles[idx]["selected"] = True
                        articles[idx]["category"] = cat
                        selected_articles.append(articles[idx])
                        print(f"  ✓ Added: {articles[idx]['title'][:50]}")
            except ValueError:
                print("  ⚠️ Invalid input, skipping category")
    
    # Save selections
    review_data["selected"] = selected_articles
    
    with open(review_file, 'w', encoding='utf-8') as f:
        json.dump(review_data, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ Selected {len(selected_articles)} articles")
    print("=" * 60)
    print("\nNext: Run 'python src/cli.py compose' to generate newsletter")


# =============================================================================
# STEP 3: COMPOSE - Generate newsletter from selections
# =============================================================================

def cmd_compose(args):
    """Generate newsletter from selected articles."""
    import webbrowser
    
    output_dir = get_output_dir()
    review_file = output_dir / f"review_{get_today_str()}.json"
    
    if not review_file.exists():
        print("❌ No review file found. Run 'scout' then 'curate' first.")
        return
    
    with open(review_file, 'r', encoding='utf-8') as f:
        review_data = json.load(f)
    
    selected = review_data.get("selected", [])
    
    if not selected:
        print("❌ No articles selected. Run 'curate' first.")
        return
    
    print("=" * 60)
    print("📧 COMPOSE: Generating Newsletter")
    print("=" * 60)
    print(f"\nGenerating newsletter with {len(selected)} selected articles...")

    try:
        config = load_config()
    except ConfigError as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Check for API key for summaries
    api_key = os.getenv('GEMINI_API_KEY')
    
    if api_key and not args.no_ai:
        print("\n🤖 Generating AI summaries...")
        from sources.rss_fetcher import Article
        
        # Convert selected articles back to Article objects
        articles = []
        for a in selected:
            from datetime import datetime
            pub_date = datetime.fromisoformat(a["published"]) if a.get("published") else None
            article = Article(
                title=a["title"],
                url=a["url"],
                source=a["source"],
                published=pub_date,
                summary=a["summary"],
                category=a.get("category", ""),
                score=a["score"]
            )
            articles.append(article)
        
        # Summarize
        articles = summarize_articles(articles, config)
    else:
        print("\n⏭️ Skipping AI summaries (no API key or --no-ai)")
        from sources.rss_fetcher import Article
        articles = []
        for a in selected:
            from datetime import datetime
            pub_date = datetime.fromisoformat(a["published"]) if a.get("published") else None
            article = Article(
                title=a["title"],
                url=a["url"],
                source=a["source"],
                published=pub_date,
                summary=a["summary"],
                category=a.get("category", ""),
                score=a["score"]
            )
            articles.append(article)
    
    # Generate HTML
    print("\n📝 Formatting newsletter...")
    html = format_newsletter_html(articles, config)
    
    # Save
    output_file = save_newsletter(html, output_dir)
    
    print("\n" + "=" * 60)
    print("✅ NEWSLETTER COMPLETE!")
    print("=" * 60)
    print(f"\n📄 File: {output_file}")
    
    if args.preview:
        print("🌐 Opening in browser...")
        webbrowser.open(f'file://{output_file.absolute()}')
    
    print("\nTo use in Outlook:")
    print("  1. Open the HTML file in your browser")
    print("  2. Select all (Ctrl+A) and copy (Ctrl+C)")
    print("  3. Paste into a new Outlook email")


# =============================================================================
# QUICK: One-shot view of top articles
# =============================================================================

def cmd_quick(args):
    """Quick view of top articles without saving."""
    print("=" * 60)
    print("⚡ QUICK VIEW: Top Articles This Week")
    print("=" * 60)

    try:
        config = load_config()
    except ConfigError as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Fetch and score
    articles = fetch_all_articles(config)
    scored = score_articles(articles, config)
    
    # Group by category
    categories = {}
    for article in scored:
        cat = article.category or "uncategorized"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(article)
    
    # Print top 3 per category
    print("\n🏆 TOP ARTICLES BY CATEGORY\n")
    
    for cat in sorted(categories.keys()):
        print(f"\n{'='*50}")
        print(f"📂 {cat.upper()}")
        print(f"{'='*50}")
        
        for article in categories[cat][:3]:
            print(f"\n  ⭐ [{article.score:.1f}] {article.title}")
            print(f"     📰 {article.source}")
            print(f"     🔗 {article.url[:60]}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='AI Newsletter Bot - Article Curation CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Workflow:
  1. scout   - Fetch and score articles from all sources
  2. curate  - Interactively select articles by category  
  3. compose - Generate newsletter from selected articles

Quick commands:
  quick     - View top articles without saving
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Scout command
    scout_parser = subparsers.add_parser('scout', help='Fetch and score articles')
    
    # Curate command  
    curate_parser = subparsers.add_parser('curate', help='Select articles interactively')
    
    # Compose command
    compose_parser = subparsers.add_parser('compose', help='Generate newsletter')
    compose_parser.add_argument('--preview', action='store_true', help='Open in browser')
    compose_parser.add_argument('--no-ai', action='store_true', help='Skip AI summaries')
    
    # Quick command
    quick_parser = subparsers.add_parser('quick', help='Quick view of top articles')
    
    args = parser.parse_args()
    
    if args.command == 'scout':
        cmd_scout(args)
    elif args.command == 'curate':
        cmd_curate(args)
    elif args.command == 'compose':
        cmd_compose(args)
    elif args.command == 'quick':
        cmd_quick(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
