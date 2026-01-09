# Testing Guide - Section-Based Newsletter Generator

## Overview

This guide covers how to test the new section-based newsletter generator with real data.

## Test Methods

### Method 1: Run End-to-End Tests (No API Key Required)

**What it does**: Validates all components with sample articles

```bash
cd "C:\Users\scott\coding projects\AI-newsletter-bot"
python -m unittest tests.test_integration_e2e -v
```

**Output**:
- ✅ All tests pass (6 tests)
- Generated sample HTML newsletter
- Validates section classification, selection rules, HTML format

**Time**: ~5 seconds
**API Key needed**: No

---

### Method 2: Generate Real Newsletter (With GEMINI_API_KEY)

**What it does**: Fetches real articles from your feeds and generates full newsletter

**Setup**:
```bash
# Set your API key
set GEMINI_API_KEY=your_actual_gemini_key
```

**Create test script** (`test_real_newsletter.py`):

```python
#!/usr/bin/env python3
"""
Test script to generate a real newsletter from your configured feeds.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.loader import load_config
from sources.rss_fetcher import fetch_articles
from sources.google_alerts import fetch_google_alerts
from services.newsletter_service import NewsletterService

def test_real_newsletter():
    """Generate a real newsletter from configured sources."""

    print("=" * 60)
    print("🚀 TESTING REAL NEWSLETTER GENERATION")
    print("=" * 60)

    # Load configuration
    print("\n📂 Loading configuration...")
    config = load_config()

    # Create newsletter service
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)

    service = NewsletterService(config, output_dir)

    # Fetch articles from configured sources
    print("\n🔍 Fetching articles from RSS feeds...")
    all_articles = []

    # Fetch from RSS feeds
    for feed_config in config.get('rss_feeds', []):
        print(f"   - Fetching from {feed_config.get('name', 'Unknown')}...")
        articles = fetch_articles([feed_config])
        all_articles.extend(articles)
        print(f"     ✓ Got {len(articles)} articles")

    # Fetch from Google Alerts
    for alert_config in config.get('google_alerts', []):
        print(f"   - Fetching from {alert_config.get('name', 'Unknown')}...")
        articles = fetch_google_alerts([alert_config])
        all_articles.extend(articles)
        print(f"     ✓ Got {len(articles)} articles")

    print(f"\n📊 Total articles fetched: {len(all_articles)}")

    if not all_articles:
        print("⚠️  No articles found. Check your feeds are working.")
        return

    # Generate newsletter with new section-based format
    print("\n🤖 Generating section-based newsletter...")
    selected = service.enrich_articles_with_sections(all_articles)

    # Generate HTML
    print("\n📝 Formatting HTML...")
    html = service.generate_newsletter_html_sections(selected)

    # Save newsletter
    print("\n💾 Saving newsletter...")
    date = datetime.now().strftime('%Y-%m-%d')
    newsletter_path = service.save_newsletter(html, date=date)

    print(f"\n✅ Newsletter saved to: {newsletter_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("📰 NEWSLETTER SUMMARY")
    print("=" * 60)
    print(f"Headlines:    {len(selected['headlines'])} articles")
    print(f"Bright Spots: {len(selected['bright_spots'])} articles")
    print(f"Tools:        {len(selected['tools'])} articles")
    print(f"Deep Dives:   {len(selected['deep_dives'])} articles")
    print(f"Grain Quality:{len(selected['grain_quality'])} articles")
    print("=" * 60)

    # Show first headline as example
    if selected['headlines']:
        article = selected['headlines'][0]
        print(f"\n📌 Example Headline Article:")
        print(f"   Title: {article.title[:60]}...")
        print(f"   Summary preview: {article.ai_summary[:100] if article.ai_summary else 'N/A'}...")
        print(f"   Canadian context: {article.canadian_context[:100] if article.canadian_context else 'N/A'}...")
        print(f"   Sentiment: {article.sentiment}")

if __name__ == '__main__':
    try:
        test_real_newsletter()
        print("\n✨ Test completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
```

**Run it**:
```bash
python test_real_newsletter.py
```

**Output**:
- Fetches from your actual configured feeds
- Generates real newsletter with Gemini summaries
- Shows summary of articles per section
- Saves HTML file

**Time**: 30-60 seconds (depends on feed size and Gemini API)
**API Key needed**: Yes (GEMINI_API_KEY)

---

### Method 3: Compare Against Your Sample Newsletters

**What it does**: Validates that generated newsletter matches your style

**Steps**:

1. Generate a newsletter using Method 2
2. Open the generated newsletter in a browser
3. Compare against your sample newsletters:
   - `C:\Users\scott\OneDrive\Desktop\drive-download-20260109T180554Z-1-001\AI This Week _ Key AI Developments You Should Know - 2025-12-04.pdf`
   - `C:\Users\scott\OneDrive\Desktop\drive-download-20260109T180554Z-1-001\AI This Week _ Key AI Developments You Should Know - 2025-11-21.pdf`

**Checklist**:

- [ ] **Structure matches**
  - [ ] Greeting: "Hello, Here's your weekly update on the latest in AI."
  - [ ] Sections in order: Headlines → Bright Spots → Tools → Learning → Deep Dives → (Grain Quality if applicable)
  - [ ] Headers with emojis (📰, ✨, 🛠️, 📚, 📊, 🌾)

- [ ] **Summary format matches**
  - [ ] 2-3 paragraphs per headline (not 3-4 sentences)
  - [ ] Paragraph 1: Who/What with numbers
  - [ ] Paragraph 2: Context & Implications
  - [ ] Paragraph 3: Canadian angle

- [ ] **Voice matches**
  - [ ] Professional but accessible (not academic)
  - [ ] Uses hedging language ("could", "may", "highlights")
  - [ ] Explains WHY (not just WHAT)
  - [ ] Balanced (acknowledges opportunities AND concerns)
  - [ ] Specific data points (numbers, percentages)

- [ ] **Content selection matches**
  - [ ] Canadian government story included
  - [ ] Governance/regulation story included
  - [ ] Mix of governance and capability articles
  - [ ] Positive stories in Bright Spots section

---

### Method 4: Test Individual Components

**Test Section Classifier**:
```bash
python -m unittest tests.test_section_based_newsletter.TestSectionClassifier -v
```

**Test Article Selector**:
```bash
python -m unittest tests.test_section_based_newsletter.TestArticleSelector -v
```

**Test Prompts**:
```bash
python -m unittest tests.test_section_based_newsletter.TestPrompts -v
```

**Test HTML Formatting**:
```bash
python -m unittest tests.test_section_based_newsletter.TestHTMLFormatting -v
```

---

### Method 5: Test Via Web API (If Deployed)

If your bot is running on Railway at `https://web-production-1cfc.up.railway.app/`:

**1. Check health endpoint**:
```bash
curl https://web-production-1cfc.up.railway.app/health
```

**2. Fetch articles** (with password):
```bash
curl -u :YOUR_PASSWORD https://web-production-1cfc.up.railway.app/fetch
```

**3. Generate newsletter**:
```bash
curl -u :YOUR_PASSWORD https://web-production-1cfc.up.railway.app/generate
```

**4. View progress**:
```bash
curl https://web-production-1cfc.up.railway.app/api/progress
```

---

## Expected Results

### Success Indicators ✅

- All unit tests pass (19 tests)
- All integration tests pass (6 tests)
- Generated HTML includes all required sections
- Headlines have 2-3 paragraph summaries
- Canadian context present in articles
- Newsletter matches your voice and structure
- Sentiment balance warnings logged (40% concerns, 35% opportunities)

### Common Issues

**Issue**: "GEMINI_API_KEY not set"
- **Fix**: Set environment variable before running
- Windows: `set GEMINI_API_KEY=your_key`
- Linux/Mac: `export GEMINI_API_KEY=your_key`

**Issue**: "No articles found"
- **Fix**: Check your RSS feeds are configured and accessible
- Test feeds manually: Open feed URLs in browser

**Issue**: "Sentiment imbalance warnings"
- **Normal**: This is expected without Gemini API (uses keyword-based detection)
- With API key: Sentiment detection will be more accurate

**Issue**: "No bright spot stories found"
- **Normal**: Depends on article content
- Solution: More positive articles in feeds

---

## Full Testing Checklist

Use this to track testing progress:

```
UNIT TESTS
- [ ] Run: python -m unittest tests.test_section_based_newsletter -v
- [ ] All 19 tests pass

INTEGRATION TESTS
- [ ] Run: python -m unittest tests.test_integration_e2e -v
- [ ] All 6 tests pass

REAL DATA TESTS
- [ ] Set GEMINI_API_KEY environment variable
- [ ] Run test_real_newsletter.py
- [ ] Newsletter generated successfully
- [ ] Article counts per section reasonable

VALIDATION TESTS
- [ ] Generated HTML opens in browser
- [ ] Structure matches sample newsletters
- [ ] Summaries are 2-3 paragraphs
- [ ] Voice is professional and analytical
- [ ] Canadian content included
- [ ] Sentiment balance logged

SMOKE TESTS (if deployed)
- [ ] Health endpoint responds
- [ ] Fetch endpoint works
- [ ] Generate endpoint works
- [ ] Progress endpoint works
```

---

## Recommended Testing Order

1. **Start here**: Run unit tests (Method 1)
   - Takes 5 seconds
   - No API key needed
   - Validates core logic

2. **Then**: Run integration tests (Method 1)
   - Takes 5 seconds
   - No API key needed
   - Validates full workflow

3. **Next**: Test with real data (Method 2)
   - Takes 30-60 seconds
   - Needs GEMINI_API_KEY
   - Uses your actual feeds

4. **Finally**: Compare with samples (Method 3)
   - Manual review
   - Validates voice and structure
   - Most important for quality

---

## Questions to Answer

After testing, you should be able to answer:

- ✅ Does the newsletter structure match your samples?
- ✅ Are summaries 2-3 paragraphs (not sentences)?
- ✅ Is the voice professional and analytical?
- ✅ Does every article have Canadian context?
- ✅ Is governance content prioritized?
- ✅ Are bright spots actually positive?
- ✅ Does the HTML render correctly?
- ✅ Are section counts reasonable?

**If yes to all: You're ready for production! 🚀**

---

## Next Steps

Once testing validates everything:

1. **Schedule automated generation**
   - Thursdays 9-10 AM (before your send day)
   - Or on-demand via web interface

2. **Set up email delivery**
   - Currently saves to file
   - Can integrate with email service

3. **Monitor performance**
   - Track article selection accuracy
   - Monitor Gemini API costs
   - Adjust configuration as needed

4. **Iterate on voice**
   - Review early newsletters
   - Fine-tune prompts if needed
   - Adjust content selection rules
