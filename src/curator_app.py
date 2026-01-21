#!/usr/bin/env python3
"""
Newsletter Curator - Article Curation Web Interface

A focused web app for curating newsletter articles into sections
and generating Outlook-compatible HTML email output.

Usage:
    python -m src.curator_app
    
Opens browser to http://127.0.0.1:5000
"""

import json
import logging
import os
import webbrowser
from datetime import datetime
from pathlib import Path
from threading import Timer

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system env vars

from flask import Flask, render_template_string, request, jsonify, redirect, url_for, Response, session, abort
from functools import wraps
import secrets

# Import Kanban template
from src.templates.kanban_template import KANBAN_TEMPLATE

# Import rate limiter for AI endpoints
from src.rate_limiter import rate_limit

# Import security dashboard
from src.security_dashboard import register_security_routes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())

@app.before_request
def csrf_protection():
    if not session.get('csrf_token'):
        session['csrf_token'] = secrets.token_hex(32)

    if request.method == "POST":
        token = session.get('csrf_token')
        submitted_token = request.form.get('csrf_token') or \
                          request.headers.get('X-CSRFToken') or \
                          (request.is_json and request.json and request.json.get('csrf_token'))

        if not token or token != submitted_token:
            abort(403)

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=session.get('csrf_token'))

# Password protection - set AUTH_PASSWORD env var for cloud deployment
AUTH_PASSWORD = os.environ.get('AUTH_PASSWORD', '')


def check_auth(password):
    """Check if the password is correct."""
    return password == AUTH_PASSWORD


def authenticate():
    """Send 401 response to prompt for password."""
    return Response(
        'Password required to access this site.\n'
        'Please enter the password.',
        401,
        {'WWW-Authenticate': 'Basic realm="Newsletter Curator"'}
    )


def requires_auth(f):
    """Decorator to require password on routes (only if AUTH_PASSWORD is set)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if AUTH_PASSWORD:  # Only check if password is configured
            auth = request.authorization
            if not auth or not check_auth(auth.password):
                return authenticate()
        return f(*args, **kwargs)
    return decorated

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# Newsletter sections in display order
SECTIONS = [
    {"id": "headlines", "name": "📰 Headlines", "color": "#667eea"},
    {"id": "bright_spots", "name": "✨ Bright Spots", "color": "#38ef7d"},
    {"id": "tools", "name": "🛠️ Tools", "color": "#f093fb"},
    {"id": "deep_dives", "name": "📊 Deep Dives", "color": "#4facfe"},
    {"id": "grain_quality", "name": "🌾 Grain Quality", "color": "#ffecd2"},
    {"id": "learning", "name": "📚 Learning", "color": "#a18cd1"},
]

# In-memory assignments (section_id -> list of article indices)
assignments = {s["id"]: [] for s in SECTIONS}
theme_of_week = {"title": "", "content": "", "enabled": False}


# Canadian keywords for detection
CANADIAN_KEYWORDS = [
    'canada', 'canadian', 'toronto', 'montreal', 'vancouver', 'ottawa',
    'alberta', 'ontario', 'quebec', 'british columbia', 'saskatchewan',
    'manitoba', 'federal', 'cifar', 'vector institute', 'mila', 'amii',
    'winnipeg', 'calgary', 'edmonton', 'halifax', 'aida', 'bill c-27'
]


def is_canadian_content(article: dict) -> bool:
    """Check if article contains Canadian content."""
    text = ' '.join([
        article.get('title', ''),
        article.get('summary', ''),
        article.get('source', '')
    ]).lower()
    return any(kw in text for kw in CANADIAN_KEYWORDS)


def clean_html_text(text: str) -> str:
    """Strip HTML tags and decode HTML entities."""
    import html
    import re
    if not text:
        return ""
    # Remove HTML tags like <b>, </b>, <strong>, etc.
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities like &amp; -> &, &lt; -> <
    text = html.unescape(text)
    return text.strip()


def load_raw_intel():
    """Load articles from raw_intel.json"""
    raw_path = DATA_DIR / "raw_intel.json"
    if not raw_path.exists():
        return []
    
    with open(raw_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    articles = data.get("articles", [])
    # Add index, Canadian flag, and clean HTML
    for i, article in enumerate(articles):
        article["_index"] = i
        article["title"] = clean_html_text(article.get("title", ""))
        article["summary"] = clean_html_text(article.get("summary", ""))
        article["_is_canadian"] = is_canadian_content(article)
    return articles


# Store AI scores in memory (persisted to scores.json)
_article_scores = {}


def load_article_scores():
    """Load previously computed AI scores."""
    global _article_scores
    scores_path = DATA_DIR / "article_scores.json"
    if scores_path.exists():
        with open(scores_path, 'r', encoding='utf-8') as f:
            _article_scores = json.load(f)
    return _article_scores


def save_article_scores():
    """Save AI scores to file."""
    scores_path = DATA_DIR / "article_scores.json"
    with open(scores_path, 'w', encoding='utf-8') as f:
        json.dump(_article_scores, f, indent=2)


def score_articles_with_ai(articles: list, max_to_score: int = 100) -> dict:
    """
    Score articles using Gemini AI. Only scores the top priority articles.
    
    Priority order: Canadian > Governance > Recent
    """
    import os
    try:
        import google.generativeai as genai
    except ImportError:
        logger.error("google-generativeai not installed")
        return {}
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY not set")
        return {}
    
    genai.configure(api_key=api_key)
    
    # Sort articles by priority: Canadian first, then governance, then recent
    def priority_sort(a):
        score = 0
        if a.get('_is_canadian'):
            score += 1000
        category = a.get('category', '').lower()
        source = a.get('source', '').lower()
        if 'governance' in category or 'governance' in source:
            score += 500
        if 'canada' in source:
            score += 300
        # More recent is better (use published date)
        return score
    
    sorted_articles = sorted(articles, key=priority_sort, reverse=True)
    to_score = sorted_articles[:max_to_score]
    
    logger.info(f"🤖 AI Scoring {len(to_score)} priority articles...")
    
    scores = {}
    model = genai.GenerativeModel('models/gemini-2.0-flash')
    
    for i, article in enumerate(to_score):
        idx = article.get('_index')
        title = article.get('title', '')[:100]
        summary = article.get('summary', '')[:300]
        source = article.get('source', '')
        
        # Skip if already scored
        if str(idx) in _article_scores:
            scores[str(idx)] = _article_scores[str(idx)]
            continue
        
        prompt = f"""You are scoring articles for "AI This Week" - a Canadian government newsletter.

Article: {title}
Source: {source}
Summary: {summary}

AUDIENCE: Canadian government professionals, policymakers, public sector AI practitioners.

SCORING (1-10):
- 9-10: Canadian government, AIDA/Bill C-27, Canadian AI policy
- 7-8: AI governance, ethics, responsible AI, public sector
- 5-6: General AI news with practical relevance
- 3-4: US-centric without Canadian relevance
- 1-2: Academic papers, deep technical content

IMPORTANT: Canadian content gets +2 bonus. Academic/technical papers get -2 penalty.

Respond in JSON ONLY:
{{"score": 7, "section": "headlines", "reason": "Brief reason"}}

Sections: headlines, bright_spots, tools, deep_dives, grain_quality, learning"""

        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            
            # Clean JSON
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            
            result = json.loads(text)
            scores[str(idx)] = {
                'score': int(result.get('score', 5)),
                'section': result.get('section', 'headlines'),
                'reason': result.get('reason', '')[:100]
            }
            _article_scores[str(idx)] = scores[str(idx)]
            
            if (i + 1) % 10 == 0:
                logger.info(f"   Scored {i + 1}/{len(to_score)} articles...")
                
        except Exception as e:
            logger.warning(f"Score failed for article {idx}: {e}")
            scores[str(idx)] = {'score': 5, 'section': 'headlines', 'reason': 'Error'}
    
    # Save scores
    save_article_scores()
    logger.info(f"✅ Scored {len(scores)} articles")
    
    return scores


def save_curated_report():
    """Save current assignments to curated_report.json"""
    articles = load_raw_intel()
    
    report = {}
    for section in SECTIONS:
        section_id = section["id"]
        section_articles = []
        for idx in assignments.get(section_id, []):
            if 0 <= idx < len(articles):
                article = articles[idx]
                section_articles.append({
                    "title": article.get("title", ""),
                    "link": article.get("link", ""),
                    "summary": article.get("summary", ""),
                    "source": article.get("source", "")
                })
        report[section_id] = section_articles
    
    # Add theme of week
    report["theme_of_week"] = theme_of_week
    
    output_path = DATA_DIR / "curated_report.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4)
    
    return output_path


def generate_email_html():
    """Generate Outlook-compatible HTML email"""
    from src.formatters.email_formatter import format_paragraphs
    
    # Load curated report
    report_path = DATA_DIR / "curated_report.json"
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    today = datetime.now()
    week_of = today.strftime("%B %d, %Y")
    
    # Build section HTML
    sections_html = ""
    
    section_configs = [
        ("headlines", "📰 HEADLINE SUMMARY", "#1a1a2e"),
        ("bright_spots", "✨ BRIGHT SPOT OF THE WEEK", "#1a1a2e"),
        ("tools", "🛠️ TOOL OF THE WEEK", "#1a1a2e"),
        ("deep_dives", "📊 DEEP DIVE", "#1a1a2e"),
        ("grain_quality", "🌾 AI & GRAIN QUALITY", "#1a1a2e"),
        ("learning", "📚 LEARNING", "#1a1a2e"),
    ]
    
    for section_id, section_title, color in section_configs:
        articles = report.get(section_id, [])
        if not articles:
            continue
        
        # Section header
        sections_html += f'''
        <tr>
            <td style="padding: 20px 30px 10px 30px;">
                <h2 style="color: {color}; margin: 0; font-size: 18px; font-weight: 700;">
                    {section_title}
                </h2>
            </td>
        </tr>
        '''
        
        # Articles
        for article in articles:
            summary = article.get("summary", "")
            sections_html += f'''
        <tr>
            <td style="padding: 15px 30px; border-bottom: 1px solid #eee;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                    <tr>
                        <td valign="top" width="100%">
                            <h3 style="color: #1a1a2e; margin: 0 0 10px 0; font-size: 15px; font-weight: 600; line-height: 1.4;">
                                🔹 <a href="{article.get('link', '#')}" style="color: #1a1a2e; text-decoration: none;">{article.get('title', '')}</a>
                            </h3>
                            <p style="color: #444444; margin: 0 0 12px 0; font-size: 14px; line-height: 1.6;">{summary}</p>
                            <p style="margin: 0; margin-top: 8px;">
                                <span style="color: #888888; font-size: 12px;">{article.get('source', '')}</span>
                                <span style="color: #cccccc;"> | </span>
                                <a href="{article.get('link', '#')}" style="color: #667eea; text-decoration: none; font-size: 12px; font-weight: 500;">Read more →</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
            '''
    
    # Theme of week
    theme = report.get("theme_of_week", {})
    theme_html = ""
    if theme.get("enabled") and theme.get("content"):
        theme_html = f'''
        <tr>
            <td style="padding: 0;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px 30px;">
                            <h2 style="color: #ffffff; margin: 0 0 5px 0; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; opacity: 0.8;">💡 Theme of the Week</h2>
                            <h3 style="color: #ffffff; margin: 0 0 15px 0; font-size: 20px; font-weight: 600; line-height: 1.3;">{theme.get('title', '')}</h3>
                            <p style="color: #e8e8ff; margin: 0; font-size: 15px; line-height: 1.7; font-style: italic;">{theme.get('content', '')}</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        '''
    
    # Complete HTML
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI This Week - {week_of}</title>
    <!--[if mso]>
    <style type="text/css">
        body, table, td {{font-family: Arial, Helvetica, sans-serif !important;}}
    </style>
    <![endif]-->
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f4f4f4;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
        <tr>
            <td align="center" style="padding: 20px 10px;">
                <table role="presentation" width="650" cellspacing="0" cellpadding="0" border="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background-color: #1a1a2e; padding: 35px 30px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700;">
                                🤖 AI This Week
                            </h1>
                            <p style="color: #a0a0a0; margin: 10px 0 0 0; font-size: 14px;">Key AI Developments for Canadian Professionals</p>
                        </td>
                    </tr>
                    
                    <!-- Intro -->
                    <tr>
                        <td style="padding: 25px 30px; border-bottom: 1px solid #eee;">
                            <p style="color: #444444; margin: 0; font-size: 15px; line-height: 1.6;">
                                <strong>Hello,</strong>
                            </p>
                            <p style="color: #444444; margin: 10px 0 0 0; font-size: 15px; line-height: 1.6;">
                                Here's your weekly update on the latest in AI.
                            </p>
                            <p style="color: #888888; margin: 10px 0 0 0; font-size: 13px;">
                                📅 Week of {week_of}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Sections -->
                    {sections_html}
                    
                    <!-- Theme of Week -->
                    {theme_html}
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #1a1a2e; padding: 25px 30px; text-align: center;">
                            <p style="color: #888888; margin: 0 0 5px 0; font-size: 12px;">
                                Curated by Scott Hazlitt
                            </p>
                            <p style="color: #666666; margin: 0; font-size: 11px;">
                                {today.strftime("%B %d, %Y")}
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''
    
    # Save HTML
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"AI_This_Week_{today.strftime('%Y-%m-%d')}.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_path, html


# ============================================================================
# HTML TEMPLATE
# ============================================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Newsletter Curator</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        header {
            text-align: center;
            padding: 20px 0;
            border-bottom: 1px solid #333;
            margin-bottom: 20px;
        }
        header h1 { font-size: 2rem; color: #fff; margin-bottom: 5px; }
        header p { color: #888; font-size: 1rem; }
        
        .main-layout {
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 20px;
        }
        
        .articles-panel {
            background: #1e1e30;
            border-radius: 12px;
            padding: 20px;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        .articles-panel h2 {
            color: #fff;
            font-size: 1.2rem;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .article-count {
            background: #667eea;
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.85rem;
        }
        
        .article-item {
            background: #252540;
            border-radius: 8px;
            padding: 12px 15px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.2s;
            border: 2px solid transparent;
        }
        .article-item:hover { background: #2a2a50; }
        .article-item.selected { border-color: #667eea; background: rgba(102, 126, 234, 0.2); }
        
        .article-title {
            font-size: 0.95rem;
            color: #fff;
            margin-bottom: 5px;
            line-height: 1.3;
        }
        .article-link {
            color: #fff;
            text-decoration: none;
            transition: color 0.2s;
        }
        .article-link:hover {
            color: #667eea;
            text-decoration: underline;
        }
        .article-summary {
            font-size: 0.85rem;
            color: #ddd;
            line-height: 1.5;
            margin: 10px 0;
            padding: 12px;
            background: rgba(102, 126, 234, 0.15);
            border-radius: 6px;
            border-left: 4px solid #667eea;
            font-style: italic;
        }
        .article-meta {
            font-size: 0.8rem;
            color: #888;
        }
        .article-source {
            color: #667eea;
        }
        
        .sections-panel {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .section-box {
            background: #1e1e30;
            border-radius: 12px;
            padding: 15px;
            border-left: 4px solid;
        }
        
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .section-title {
            font-size: 1rem;
            color: #fff;
            font-weight: 600;
        }
        .section-count {
            background: rgba(255,255,255,0.1);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8rem;
        }
        
        .section-articles {
            font-size: 0.85rem;
            color: #aaa;
        }
        .section-article {
            padding: 5px 0;
            border-bottom: 1px solid #333;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .section-article:last-child { border-bottom: none; }
        .remove-btn {
            background: #ff4757;
            border: none;
            color: white;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 0.7rem;
        }
        
        .actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        .btn {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            font-weight: 600;
        }
        .btn-generate {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }
        .btn-preview {
            background: #333;
            color: white;
        }
        
        .assign-dropdown {
            background: #333;
            border: 1px solid #444;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.8rem;
            cursor: pointer;
        }
        
        .theme-section {
            background: #1e1e30;
            border-radius: 12px;
            padding: 15px;
            margin-top: 15px;
        }
        .theme-section h3 {
            color: #fff;
            font-size: 1rem;
            margin-bottom: 10px;
        }
        .theme-input {
            width: 100%;
            background: #252540;
            border: 1px solid #333;
            color: white;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 10px;
            font-family: inherit;
        }
        .theme-textarea {
            min-height: 80px;
            resize: vertical;
        }
        .theme-toggle {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.9rem;
        }
        
        .search-box {
            width: 100%;
            padding: 10px 15px;
            background: #252540;
            border: 1px solid #333;
            border-radius: 8px;
            color: white;
            font-size: 0.95rem;
            margin-bottom: 10px;
        }
        .search-box:focus { outline: none; border-color: #667eea; }
        
        .filter-controls {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        .filter-tabs {
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
            flex: 1;
        }
        .filter-tab {
            padding: 6px 12px;
            background: #333;
            border: none;
            border-radius: 15px;
            color: #aaa;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .filter-tab:hover { background: #444; color: #fff; }
        .filter-tab.active { background: #667eea; color: white; }
        .filter-tab .count {
            background: rgba(255,255,255,0.2);
            padding: 1px 6px;
            border-radius: 10px;
            margin-left: 5px;
            font-size: 0.75rem;
        }
        
        .sort-select {
            padding: 6px 12px;
            background: #333;
            border: 1px solid #444;
            border-radius: 6px;
            color: white;
            font-size: 0.8rem;
            cursor: pointer;
        }
        
        .canadian-badge {
            display: inline-block;
            background: linear-gradient(135deg, #ff0000, #fff, #ff0000);
            color: #000;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            margin-left: 5px;
        }
        
        .article-item.canadian {
            border-left: 3px solid #ff0000;
        }
        
        .score-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 5px;
        }
        .score-high { background: linear-gradient(135deg, #11998e, #38ef7d); color: white; }
        .score-med { background: linear-gradient(135deg, #f093fb, #f5576c); color: white; }
        .score-low { background: #333; color: #888; }
        
        .btn-score {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-autofill {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }
        
        .btn-theme-gen {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            font-size: 0.8rem;
            padding: 5px 10px;
            margin-left: 10px;
        }
        
        .scoring-status {
            text-align: center;
            padding: 10px;
            background: rgba(102, 126, 234, 0.2);
            border-radius: 6px;
            margin-bottom: 10px;
            display: none;
        }
        
        .assign-row {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 8px;
        }
        
        .ai-suggestion {
            font-size: 0.75rem;
            color: #9f7aea;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 Newsletter Curator</h1>
            <p>Select articles and assign to sections</p>
        </header>
        
        <div class="main-layout">
            <div class="articles-panel">
                <h2>
                    Available Articles
                    <span class="article-count" id="visible-count">{{ articles|length }}</span>
                </h2>
                <input type="text" class="search-box" placeholder="🔍 Search articles..." id="search-input" onkeyup="applyFilters()">
                
                <div class="filter-controls">
                    <div class="filter-tabs">
                        <button class="filter-tab active" data-category="all" onclick="setCategory('all')">All</button>
                        <button class="filter-tab" data-category="google_alerts" onclick="setCategory('google_alerts')">📧 Google Alerts</button>
                        <button class="filter-tab" data-category="deep_dive" onclick="setCategory('deep_dive')">📊 Deep Dives</button>
                        <button class="filter-tab" data-category="governance" onclick="setCategory('governance')">⚖️ Governance</button>
                        <button class="filter-tab" data-category="business" onclick="setCategory('business')">💼 Business</button>
                        <button class="filter-tab" data-category="canadian" onclick="setCategory('canadian')">🍁 Canadian</button>
                    </div>
                    <select class="sort-select" id="sort-select" onchange="applyFilters()">
                        <option value="score">⭐ Highest Score</option>
                        <option value="newest">Newest First</option>
                        <option value="oldest">Oldest First</option>
                        <option value="source">By Source</option>
                    </select>
                </div>
                
                <div id="articles-list">
                {% for article in articles %}
                <div class="article-item {% if article._is_canadian %}canadian{% endif %}" id="article-{{ article._index }}" data-index="{{ article._index }}" data-category="{{ article.category }}" data-published="{{ article.published }}" data-canadian="{{ article._is_canadian }}">
                    <div class="article-title">
                        <a href="{{ article.link }}" target="_blank" class="article-link">{{ article.title[:100] }}{% if article.title|length > 100 %}...{% endif %}</a>
                        {% if article._is_canadian %}<span class="canadian-badge">🍁 CAN</span>{% endif %}
                    </div>
                    {% if article.summary %}
                    <div class="article-summary">{{ article.summary[:150] }}{% if article.summary|length > 150 %}...{% endif %}</div>
                    {% endif %}
                    <div class="article-meta">
                        <span class="article-source">{{ article.source }}</span>
                        {% if article.published %} · {{ article.published[:16] | replace('T', ' ') }}{% endif %}
                    </div>
                    <div class="assign-row">
                        <select class="assign-dropdown" onchange="assignArticle({{ article._index }}, this.value)">
                            <option value="">Assign to section...</option>
                            {% for section in sections %}
                            <option value="{{ section.id }}">{{ section.name }}</option>
                            {% endfor %}
                        </select>
                        <span class="ai-suggestion" id="suggest-{{ article._index }}"></span>
                    </div>
                </div>
                {% endfor %}
                </div>
            </div>
            
            <div class="sections-panel">
                {% for section in sections %}
                <div class="section-box" style="border-color: {{ section.color }};" id="section-{{ section.id }}">
                    <div class="section-header">
                        <span class="section-title">{{ section.name }}</span>
                        <span class="section-count" id="count-{{ section.id }}">0</span>
                    </div>
                    <div class="section-articles" id="list-{{ section.id }}">
                        <em style="color: #666;">No articles assigned</em>
                    </div>
                </div>
                {% endfor %}
                
                <div class="theme-section">
                    <h3>💡 Theme of the Week</h3>
                    <input type="text" class="theme-input" id="theme-title" placeholder="Theme title...">
                    <textarea class="theme-input theme-textarea" id="theme-content" placeholder="Theme content..."></textarea>
                    <label class="theme-toggle">
                        <input type="checkbox" id="theme-enabled"> Enable Theme
                    </label>
                    <button class="btn btn-theme-gen" onclick="generateTheme()">✨ AI Generate</button>
                </div>
                
                <div class="actions">
                    <button class="btn btn-autofill" onclick="autoFillSections()">⚡ Auto-Fill</button>
                    <button class="btn btn-score" onclick="scoreArticles()" id="score-btn">🧠 AI Score</button>
                    <button class="btn btn-generate" onclick="generateNewsletter()">📧 Generate</button>
                    <button class="btn btn-preview" onclick="previewNewsletter()">👁️ Preview</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Store article data
        const articles = {{ articles_json|safe }};
        const assignments = {};
        let currentCategory = 'all';
        
        // Category mapping for filtering
        const categoryAliases = {
            'google_alerts': ['google_alerts', 'capabilities', 'governance', 'business'],
            'deep_dive': ['deep_dive', 'research'],
            'governance': ['governance'],
            'business': ['business'],
        };
        
        function setCategory(category) {
            currentCategory = category;
            
            // Update active tab
            document.querySelectorAll('.filter-tab').forEach(tab => {
                tab.classList.remove('active');
                if (tab.dataset.category === category) {
                    tab.classList.add('active');
                }
            });
            
            applyFilters();
        }
        
        function applyFilters() {
            const query = document.getElementById('search-input').value.toLowerCase();
            const sortBy = document.getElementById('sort-select').value;
            
            // Get all article items
            const items = Array.from(document.querySelectorAll('.article-item'));
            
            // Filter
            let visible = 0;
            items.forEach(item => {
                const title = item.querySelector('.article-title').textContent.toLowerCase();
                const source = item.querySelector('.article-source').textContent.toLowerCase();
                const summary = item.querySelector('.article-summary')?.textContent.toLowerCase() || '';
                const category = item.dataset.category || '';
                const isCanadian = item.dataset.canadian === 'True';
                
                // Text search
                const matchesSearch = !query || title.includes(query) || source.includes(query) || summary.includes(query);
                
                // Category filter
                let matchesCategory = true;
                if (currentCategory === 'canadian') {
                    matchesCategory = isCanadian;
                } else if (currentCategory !== 'all') {
                    const aliases = categoryAliases[currentCategory] || [currentCategory];
                    matchesCategory = aliases.some(alias => category.includes(alias) || source.toLowerCase().includes(currentCategory.replace('_', ' ')));
                }
                
                if (matchesSearch && matchesCategory) {
                    item.style.display = 'block';
                    visible++;
                } else {
                    item.style.display = 'none';
                }
            });
            
            // Update visible count
            document.getElementById('visible-count').textContent = visible;
            
            // Sort visible items
            const container = document.getElementById('articles-list');
            const visibleItems = items.filter(i => i.style.display !== 'none');
            
            visibleItems.sort((a, b) => {
                if (sortBy === 'score') {
                    const scoreA = articleScores[a.dataset.index]?.score || 0;
                    const scoreB = articleScores[b.dataset.index]?.score || 0;
                    return scoreB - scoreA;  // Highest first
                } else if (sortBy === 'newest') {
                    return (b.dataset.published || '').localeCompare(a.dataset.published || '');
                } else if (sortBy === 'oldest') {
                    return (a.dataset.published || '').localeCompare(b.dataset.published || '');
                } else {
                    return a.querySelector('.article-source').textContent.localeCompare(
                        b.querySelector('.article-source').textContent
                    );
                }
            });
            
            // Reorder DOM
            visibleItems.forEach(item => container.appendChild(item));
        }
        
        function assignArticle(index, sectionId) {
            if (!sectionId) return;
            
            // Remove from previous section if any
            for (const [sid, indices] of Object.entries(assignments)) {
                const pos = indices.indexOf(index);
                if (pos > -1) {
                    indices.splice(pos, 1);
                    updateSectionUI(sid);
                }
            }
            
            // Add to new section
            if (!assignments[sectionId]) assignments[sectionId] = [];
            if (!assignments[sectionId].includes(index)) {
                assignments[sectionId].push(index);
            }
            
            updateSectionUI(sectionId);
            
            // Mark article as assigned
            document.getElementById('article-' + index).classList.add('selected');
        }
        
        function removeFromSection(index, sectionId) {
            const indices = assignments[sectionId] || [];
            const pos = indices.indexOf(index);
            if (pos > -1) {
                indices.splice(pos, 1);
                updateSectionUI(sectionId);
                document.getElementById('article-' + index).classList.remove('selected');
                document.querySelector('#article-' + index + ' .assign-dropdown').value = '';
            }
        }
        
        function updateSectionUI(sectionId) {
            const indices = assignments[sectionId] || [];
            const countEl = document.getElementById('count-' + sectionId);
            const listEl = document.getElementById('list-' + sectionId);
            
            countEl.textContent = indices.length;
            
            if (indices.length === 0) {
                listEl.innerHTML = '<em style="color: #666;">No articles assigned</em>';
            } else {
                listEl.innerHTML = indices.map(idx => {
                    const article = articles[idx];
                    const title = article.title.substring(0, 50) + (article.title.length > 50 ? '...' : '');
                    return `<div class="section-article">
                        <span>${title}</span>
                        <button class="remove-btn" onclick="removeFromSection(${idx}, '${sectionId}')">×</button>
                    </div>`;
                }).join('');
            }
        }
        
        function generateNewsletter() {
            const theme = {
                title: document.getElementById('theme-title').value,
                content: document.getElementById('theme-content').value,
                enabled: document.getElementById('theme-enabled').checked
            };
            
            fetch('/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({assignments: assignments, theme: theme})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    alert('✅ Newsletter generated!\\n\\nFile: ' + data.path + '\\n\\nOpening preview...');
                    window.open('/preview', '_blank');
                } else {
                    alert('Error: ' + data.error);
                }
            });
        }
        
        function previewNewsletter() {
            window.open('/preview', '_blank');
        }
        
        function autoFillSections() {
            // Section limits
            const sectionLimits = {
                'headlines': 8,
                'bright_spots': 2,
                'tools': 2,
                'deep_dives': 4,
                'grain_quality': 2,
                'learning': 2
            };
            
            // Clear current assignments
            for (const sid of Object.keys(assignments)) {
                assignments[sid] = [];
            }
            
            // Get scored articles sorted by score
            const scored = Object.entries(articleScores)
                .map(([idx, data]) => ({idx: parseInt(idx), ...data}))
                .filter(a => a.score >= 5)  // Only 5+ scores
                .sort((a, b) => b.score - a.score);
            
            // Fill sections based on AI suggestions
            const sectionCounts = {};
            for (const section of Object.keys(sectionLimits)) {
                sectionCounts[section] = 0;
                if (!assignments[section]) assignments[section] = [];
            }
            
            for (const item of scored) {
                const section = item.section || 'headlines';
                const limit = sectionLimits[section] || 2;
                
                if (sectionCounts[section] < limit) {
                    if (!assignments[section].includes(item.idx)) {
                        assignments[section].push(item.idx);
                        sectionCounts[section]++;
                        
                        // Update dropdown
                        const dropdown = document.querySelector('#article-' + item.idx + ' .assign-dropdown');
                        if (dropdown) dropdown.value = section;
                        
                        // Mark as selected
                        document.getElementById('article-' + item.idx)?.classList.add('selected');
                    }
                }
            }
            
            // Update all section UIs
            for (const section of Object.keys(sectionLimits)) {
                updateSectionUI(section);
            }
            
            const total = Object.values(assignments).reduce((sum, arr) => sum + arr.length, 0);
            alert('⚡ Auto-filled ' + total + ' articles based on AI suggestions!\\n\\nReview and adjust as needed.');
        }
        
        function generateTheme() {
            const btn = document.querySelector('.btn-theme-gen');
            btn.disabled = true;
            btn.textContent = '⏳ Generating...';
            
            // Get selected article indices
            const selected = Object.values(assignments).flat();
            
            fetch('/generate-theme', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({article_indices: selected})
            })
            .then(r => r.json())
            .then(data => {
                btn.disabled = false;
                btn.textContent = '✨ AI Generate';
                
                if (data.success) {
                    document.getElementById('theme-title').value = data.title || '';
                    document.getElementById('theme-content').value = data.content || '';
                    document.getElementById('theme-enabled').checked = true;
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(err => {
                btn.disabled = false;
                btn.textContent = '✨ AI Generate';
                alert('Error: ' + err.message);
            });
        }
        
        // AI Scoring
        let articleScores = {{ scores_json|safe }};
        
        function scoreArticles() {
            const btn = document.getElementById('score-btn');
            btn.disabled = true;
            btn.textContent = '⏳ Scoring...';
            
            fetch('/score', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            })
            .then(r => r.json())
            .then(data => {
                btn.disabled = false;
                btn.textContent = '🧠 AI Score';
                
                if (data.success) {
                    articleScores = {...articleScores, ...data.scores};
                    displayScores();
                    applyFilters();  // Re-sort with scores
                    alert('✅ Scored ' + data.scored + ' articles!\\n\\nHigh-scoring articles now show score badges.');
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(err => {
                btn.disabled = false;
                btn.textContent = '🧠 AI Score';
                alert('Error: ' + err.message);
            });
        }
        
        function displayScores() {
            // Section display names
            const sectionNames = {
                'headlines': '📰 Headlines',
                'bright_spots': '✨ Bright Spots',
                'tools': '🛠️ Tools',
                'deep_dives': '📊 Deep Dives',
                'grain_quality': '🌾 Grain',
                'learning': '📚 Learning'
            };
            
            document.querySelectorAll('.article-item').forEach(item => {
                const idx = item.dataset.index;
                const scoreData = articleScores[idx];
                
                // Remove existing badge
                const existingBadge = item.querySelector('.score-badge');
                if (existingBadge) existingBadge.remove();
                
                // Update suggestion span
                const suggestEl = document.getElementById('suggest-' + idx);
                
                if (scoreData) {
                    const score = scoreData.score;
                    let badgeClass = 'score-low';
                    if (score >= 7) badgeClass = 'score-high';
                    else if (score >= 4) badgeClass = 'score-med';
                    
                    const badge = document.createElement('span');
                    badge.className = 'score-badge ' + badgeClass;
                    badge.textContent = score + '/10';
                    badge.title = scoreData.reason || '';
                    
                    const titleEl = item.querySelector('.article-title');
                    titleEl.appendChild(badge);
                    
                    // Add suggested section as data attribute
                    item.dataset.suggestedSection = scoreData.section || '';
                    
                    // Display suggestion next to dropdown
                    if (suggestEl && scoreData.section) {
                        const displayName = sectionNames[scoreData.section] || scoreData.section;
                        suggestEl.textContent = 'AI suggests: ' + displayName;
                    }
                } else if (suggestEl) {
                    suggestEl.textContent = '';
                }
            });
        }
        
        // Load existing scores on page load
        window.addEventListener('load', displayScores);
        
        // AUTO-CURATE: Automatically score, fill, and generate theme on load
        async function autoCurate() {
            const statusDiv = document.createElement('div');
            statusDiv.id = 'auto-curate-status';
            statusDiv.style.cssText = 'position:fixed;top:20px;left:50%;transform:translateX(-50%);background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:15px 30px;border-radius:10px;z-index:9999;font-weight:600;box-shadow:0 4px 20px rgba(0,0,0,0.3);';
            document.body.appendChild(statusDiv);
            
            const updateStatus = (msg) => { statusDiv.textContent = msg; };
            
            try {
                // Check if we need to score
                const scoredCount = Object.keys(articleScores).length;
                
                if (scoredCount < 50) {
                    updateStatus('🧠 Auto-scoring articles... (this takes 2-3 min)');
                    
                    const scoreResponse = await fetch('/score', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'}
                    });
                    const scoreData = await scoreResponse.json();
                    
                    if (scoreData.success) {
                        articleScores = {...articleScores, ...scoreData.scores};
                        displayScores();
                    }
                }
                
                updateStatus('⚡ Auto-filling sections...');
                await new Promise(r => setTimeout(r, 500));
                autoFillSections();
                
                // Check if we have selections before generating theme
                const totalSelected = Object.values(assignments).flat().length;
                if (totalSelected > 0) {
                    updateStatus('✨ Generating Theme of the Week...');
                    
                    const themeResponse = await fetch('/generate-theme', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({article_indices: Object.values(assignments).flat()})
                    });
                    const themeData = await themeResponse.json();
                    
                    if (themeData.success) {
                        document.getElementById('theme-title').value = themeData.title || '';
                        document.getElementById('theme-content').value = themeData.content || '';
                        document.getElementById('theme-enabled').checked = true;
                    }
                }
                
                updateStatus('✅ Auto-curation complete! Review and click Generate.');
                setTimeout(() => statusDiv.remove(), 3000);
                
            } catch (err) {
                updateStatus('⚠️ Auto-curate error: ' + err.message);
                setTimeout(() => statusDiv.remove(), 5000);
            }
        }
        
        // Start auto-curation after a short delay
        window.addEventListener('load', () => {
            setTimeout(autoCurate, 1000);
        });
    </script>
</body>
</html>
'''


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
@requires_auth
def index():
    """Main curation interface"""
    articles = load_raw_intel()
    scores = load_article_scores()
    return render_template_string(
        KANBAN_TEMPLATE, 
        articles=articles,
        articles_json=json.dumps(articles),
        sections=SECTIONS,
        scores_json=json.dumps(scores)
    )


@app.route('/score', methods=['POST'])
@requires_auth
@rate_limit
def score():
    """AI-score priority articles"""
    try:
        articles = load_raw_intel()
        scores = score_articles_with_ai(articles, max_to_score=100)
        return jsonify({"success": True, "scored": len(scores), "scores": scores})
    except Exception as e:
        logger.error(f"Score error: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route('/generate-theme', methods=['POST'])
@requires_auth
@rate_limit
def generate_theme_route():
    """Generate Theme of Week from selected articles using AI"""
    import os
    try:
        import google.generativeai as genai
    except ImportError:
        return jsonify({"success": False, "error": "Gemini not installed"})
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return jsonify({"success": False, "error": "GEMINI_API_KEY not set"})
    
    try:
        data = request.get_json()
        indices = data.get('article_indices', [])
        
        articles = load_raw_intel()
        selected = [articles[i] for i in indices if 0 <= i < len(articles)]
        
        if not selected:
            return jsonify({"success": False, "error": "No articles selected"})
        
        # Build article summaries for the prompt
        articles_text = "\n".join([
            f"- {a.get('title', '')[:80]}: {a.get('summary', '')[:150]}..."
            for a in selected[:10]
        ])
        
        prompt = f"""You are the editor of "AI This Week", a professional newsletter for Canadian AI professionals.

Selected articles this week:
{articles_text}

Write a "THEME OF THE WEEK" (about 100 words) that:
1. Identifies the common thread across these articles
2. Provides analytical perspective on what this means for AI
3. Speaks to Canadian professionals and policymakers

Respond in JSON:
{{"title": "A compelling 5-8 word title", "content": "Your 100-word editorial..."}}"""

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        text = response.text.strip()
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        
        result = json.loads(text)
        return jsonify({"success": True, "title": result.get('title', ''), "content": result.get('content', '')})
        
    except Exception as e:
        logger.error(f"Theme generation error: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route('/scores')
@requires_auth
def get_scores():
    """Get current article scores"""
    scores = load_article_scores()
    return jsonify(scores)


@app.route('/generate', methods=['POST'])
@requires_auth
def generate():
    """Generate newsletter from assignments"""
    global assignments, theme_of_week
    try:
        data = request.get_json()
        assignments = data.get('assignments', {})
        theme_of_week = data.get('theme', {"title": "", "content": "", "enabled": False})
        
        # Save curated report
        save_curated_report()
        
        # Generate email HTML
        output_path, _ = generate_email_html()
        
        return jsonify({"success": True, "path": str(output_path)})
    except Exception as e:
        logger.error(f"Generate error: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route('/preview')
@requires_auth
def preview():
    """Preview generated newsletter"""
    today = datetime.now().strftime('%Y-%m-%d')
    output_path = OUTPUT_DIR / f"AI_This_Week_{today}.html"
    
    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h1>No newsletter generated yet. Go back and click Generate.</h1>"


def open_browser():
    webbrowser.open('http://127.0.0.1:5000')


if __name__ == '__main__':
    # Register security dashboard routes
    register_security_routes(app)
    
    print("\n" + "=" * 50)
    print("🤖 Newsletter Curator")
    print("=" * 50)
    print("\n🌐 Opening browser at http://127.0.0.1:5000\n")
    
    Timer(1.5, open_browser).start()
    app.run(debug=False, host='127.0.0.1', port=5000)
