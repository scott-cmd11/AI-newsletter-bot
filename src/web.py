#!/usr/bin/env python3
"""
AI Newsletter Bot - Web Interface

A simple Flask web app for curating newsletter articles.
"""

import os
import json
import webbrowser
from datetime import datetime
from pathlib import Path
from threading import Timer
from functools import wraps

from flask import Flask, render_template_string, request, redirect, url_for, jsonify, Response
import yaml

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from sources.rss_fetcher import fetch_all_articles, Article
from processors.scorer import score_articles
from processors.summarizer import summarize_articles, generate_theme_of_week
from formatters.email_formatter import format_newsletter_html, save_newsletter

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Password protection - set AUTH_PASSWORD env var in Render
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
        {'WWW-Authenticate': 'Basic realm="AI Newsletter Bot"'}
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
OUTPUT_DIR = BASE_DIR / "output"
CONFIG_PATH = BASE_DIR / "config" / "sources.yaml"


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_review_file():
    return OUTPUT_DIR / f"review_{datetime.now().strftime('%Y-%m-%d')}.json"


def load_review_data():
    review_file = get_review_file()
    if review_file.exists():
        with open(review_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_review_data(data):
    review_file = get_review_file()
    with open(review_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Newsletter Bot - Article Curator</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid #333;
            margin-bottom: 30px;
        }
        header h1 {
            font-size: 2.5rem;
            color: #fff;
            margin-bottom: 10px;
        }
        header p {
            color: #888;
            font-size: 1.1rem;
        }
        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 20px 0;
        }
        .stat {
            background: rgba(102, 126, 234, 0.2);
            padding: 15px 25px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            font-size: 0.9rem;
            color: #888;
        }
        .actions {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 30px 0;
        }
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 6px;
            font-size: 1rem;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        .btn-secondary {
            background: #333;
            color: #fff;
        }
        .btn-secondary:hover {
            background: #444;
        }
        .btn-success {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }
        .category {
            background: #1e1e30;
            border-radius: 12px;
            margin-bottom: 25px;
            overflow: hidden;
        }
        .category-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 15px 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .category-header h2 {
            font-size: 1.3rem;
            color: white;
        }
        .category-header .count {
            background: rgba(255,255,255,0.2);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
        }
        .articles {
            padding: 15px;
        }
        .article {
            background: #252540;
            border-radius: 8px;
            padding: 15px 20px;
            margin-bottom: 10px;
            display: flex;
            gap: 15px;
            align-items: flex-start;
            transition: all 0.2s;
        }
        .article:hover {
            background: #2a2a50;
        }
        .article.selected {
            background: rgba(102, 126, 234, 0.3);
            border: 1px solid #667eea;
        }
        .article input[type="checkbox"] {
            width: 22px;
            height: 22px;
            margin-top: 3px;
            cursor: pointer;
            accent-color: #667eea;
        }
        .article-content {
            flex: 1;
        }
        .article-title {
            font-size: 1.1rem;
            color: #fff;
            margin-bottom: 8px;
            line-height: 1.4;
        }
        .article-title a {
            color: #fff;
            text-decoration: none;
        }
        .article-title a:hover {
            color: #667eea;
        }
        .article-meta {
            display: flex;
            gap: 15px;
            font-size: 0.85rem;
            color: #888;
        }
        .article-score {
            background: #667eea;
            color: white;
            padding: 2px 10px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.8rem;
        }
        .article-summary {
            margin-top: 10px;
            font-size: 0.9rem;
            color: #aaa;
            line-height: 1.5;
        }
        .selected-count {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 15px 25px;
            border-radius: 50px;
            box-shadow: 0 5px 30px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            gap: 15px;
            z-index: 100;
        }
        .selected-count span {
            font-size: 1.1rem;
        }
        .loading {
            text-align: center;
            padding: 50px;
        }
        .loading .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #333;
            border-top-color: #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
        }
        .empty-state h3 {
            font-size: 1.5rem;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 AI Newsletter Bot</h1>
            <p>Select articles to include in your newsletter</p>
        </header>

        {% if not data %}
        <div class="empty-state">
            <h3>No articles loaded</h3>
            <p style="margin-bottom: 20px;">Click "Fetch New Articles" to get the latest from your feeds.</p>
            <a href="{{ url_for('fetch_articles') }}" class="btn btn-primary">🔄 Fetch New Articles</a>
        </div>
        {% else %}
        
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{{ data.total_articles }}</div>
                <div class="stat-label">Total Articles</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="selected-count">{{ data.selected|length }}</div>
                <div class="stat-label">Selected</div>
            </div>
            <div class="stat">
                <div class="stat-value">{{ data.categories|length }}</div>
                <div class="stat-label">Categories</div>
            </div>
        </div>

        <div class="actions">
            <a href="{{ url_for('fetch_articles') }}" class="btn btn-secondary">🔄 Refresh Articles</a>
            <button onclick="selectTop()" class="btn btn-secondary">⭐ Auto-Select Top 8</button>
            <button onclick="generateNewsletter()" class="btn btn-success" id="generate-btn">📧 Generate Newsletter</button>
        </div>

        <form id="article-form" method="POST" action="{{ url_for('save_selection') }}">
            {% for cat_name, articles in data.categories.items() %}
            <div class="category">
                <div class="category-header">
                    <h2>
                        {% if cat_name == 'governance' %}⚖️{% elif cat_name == 'capabilities' %}🚀{% elif cat_name == 'business' %}💼{% elif cat_name == 'tools' %}🛠️{% elif cat_name == 'education' %}📚{% else %}📰{% endif %}
                        {{ cat_name|title }}
                    </h2>
                    <span class="count">{{ articles|length }} articles</span>
                </div>
                <div class="articles">
                    {% for article in articles[:10] %}
                    <div class="article {% if article.selected %}selected{% endif %}" data-score="{{ article.score }}">
                        <input type="checkbox" 
                               name="selected" 
                               value="{{ cat_name }}:{{ article.id }}"
                               {% if article.selected %}checked{% endif %}
                               onchange="updateCount()">
                        <div class="article-content">
                            <div class="article-title">
                                <a href="{{ article.url }}" target="_blank">{{ article.title }}</a>
                            </div>
                            <div class="article-meta">
                                <span class="article-score">{{ "%.1f"|format(article.score) }}</span>
                                <span>📰 {{ article.source }}</span>
                                {% if article.published %}
                                <span>📅 {{ article.published[:10] }}</span>
                                {% endif %}
                            </div>
                            <div class="article-summary">{{ article.summary[:200] }}{% if article.summary|length > 200 %}...{% endif %}</div>
                        </div>
                    </div>
                    {% endfor %}
                    {% if articles|length > 10 %}
                    <p style="text-align: center; padding: 15px; color: #666;">+ {{ articles|length - 10 }} more articles</p>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </form>
        
        <div class="selected-count" id="floating-count" style="display: none;">
            <span><strong id="float-count">0</strong> articles selected</span>
            <button onclick="generateNewsletter()" class="btn btn-primary">Generate →</button>
        </div>
        {% endif %}
    </div>

    <script>
        function updateCount() {
            const checked = document.querySelectorAll('input[name="selected"]:checked').length;
            document.getElementById('selected-count').textContent = checked;
            document.getElementById('float-count').textContent = checked;
            document.getElementById('floating-count').style.display = checked > 0 ? 'flex' : 'none';
            
            // Update visual state
            document.querySelectorAll('.article').forEach(article => {
                const checkbox = article.querySelector('input[type="checkbox"]');
                article.classList.toggle('selected', checkbox.checked);
            });
        }

        function selectTop() {
            // Uncheck all first
            document.querySelectorAll('input[name="selected"]').forEach(cb => cb.checked = false);
            
            // Get all articles with scores and sort
            const articles = Array.from(document.querySelectorAll('.article'));
            articles.sort((a, b) => parseFloat(b.dataset.score) - parseFloat(a.dataset.score));
            
            // Select top 8
            articles.slice(0, 8).forEach(article => {
                article.querySelector('input[type="checkbox"]').checked = true;
            });
            
            updateCount();
        }

        function generateNewsletter() {
            const form = document.getElementById('article-form');
            const formData = new FormData(form);
            
            // Save selections first
            fetch('{{ url_for("save_selection") }}', {
                method: 'POST',
                body: formData
            }).then(() => {
                window.location.href = '{{ url_for("generate") }}';
            });
        }

        // Initialize count
        updateCount();
    </script>
</body>
</html>
'''

LOADING_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Loading...</title>
    <style>
        body { font-family: sans-serif; background: #1a1a2e; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .loading { text-align: center; }
        .spinner { width: 50px; height: 50px; border: 4px solid #333; border-top-color: #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
    <meta http-equiv="refresh" content="2;url={{ redirect_url }}">
</head>
<body>
    <div class="loading">
        <div class="spinner"></div>
        <h2>{{ message }}</h2>
        <p>Please wait...</p>
    </div>
</body>
</html>
'''

RESULT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Newsletter Generated</title>
    <style>
        body { font-family: sans-serif; background: #1a1a2e; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .success { text-align: center; background: #252540; padding: 50px; border-radius: 16px; }
        .success h1 { color: #38ef7d; margin-bottom: 20px; }
        .btn { display: inline-block; padding: 15px 30px; margin: 10px; border-radius: 8px; text-decoration: none; font-size: 1rem; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .btn-secondary { background: #333; color: white; }
    </style>
</head>
<body>
    <div class="success">
        <h1>✅ Newsletter Generated!</h1>
        <p style="margin-bottom: 30px;">Your newsletter is ready.</p>
        <a href="{{ url_for('preview') }}" class="btn btn-primary" target="_blank">📧 View Newsletter</a>
        <a href="{{ url_for('index') }}" class="btn btn-secondary">← Back to Selection</a>
    </div>
</body>
</html>
'''


@app.route('/')
@requires_auth
def index():
    data = load_review_data()
    return render_template_string(HTML_TEMPLATE, data=data)


@app.route('/fetch')
@requires_auth
def fetch_articles():
    """Fetch and score new articles."""
    config = load_config()
    
    # Fetch articles
    articles = fetch_all_articles(config)
    scored = score_articles(articles, config)
    
    # Group by category
    categories = {}
    for article in scored:
        cat = article.category or "uncategorized"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(article)
    
    # Save for review
    review_data = {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "total_articles": len(scored),
        "categories": {},
        "selected": []
    }
    
    for cat, articles_list in categories.items():
        review_data["categories"][cat] = [
            {
                "id": i,
                "title": a.title,
                "url": a.url,
                "source": a.source,
                "score": a.score,
                "summary": a.summary[:300] if a.summary else "",
                "published": a.published.isoformat() if a.published else None,
                "selected": False
            }
            for i, a in enumerate(articles_list)
        ]
    
    save_review_data(review_data)
    return redirect(url_for('index'))


@app.route('/save', methods=['POST'])
@requires_auth
def save_selection():
    """Save article selection."""
    data = load_review_data()
    if not data:
        return redirect(url_for('index'))
    
    # Get selected articles
    selected_ids = request.form.getlist('selected')
    
    # Reset all selections
    for cat_name, articles in data['categories'].items():
        for article in articles:
            article['selected'] = False
    
    # Mark selected articles
    selected_articles = []
    for sel_id in selected_ids:
        cat_name, article_id = sel_id.split(':')
        article_id = int(article_id)
        
        if cat_name in data['categories']:
            for article in data['categories'][cat_name]:
                if article['id'] == article_id:
                    article['selected'] = True
                    article['category'] = cat_name
                    selected_articles.append(article)
                    break
    
    data['selected'] = selected_articles
    save_review_data(data)
    
    return jsonify({"status": "ok", "count": len(selected_articles)})


@app.route('/generate')
@requires_auth
def generate():
    """Generate newsletter from selected articles."""
    data = load_review_data()
    if not data or not data.get('selected'):
        return redirect(url_for('index'))
    
    config = load_config()
    selected = data['selected']
    
    # Convert to Article objects
    articles = []
    for a in selected:
        pub_date = None
        if a.get('published'):
            try:
                pub_date = datetime.fromisoformat(a['published'])
            except:
                pass
        
        article = Article(
            title=a['title'],
            url=a['url'],
            source=a['source'],
            published=pub_date,
            summary=a['summary'],
            category=a.get('category', ''),
            score=a.get('score', 0)
        )
        articles.append(article)
    
    # Generate AI summaries if API key available
    api_key = os.getenv('GEMINI_API_KEY')
    theme_of_week = None
    if api_key:
        articles = summarize_articles(articles, config)
        # Generate Theme of the Week
        theme_of_week = generate_theme_of_week(articles, config)
    
    # Generate HTML
    html = format_newsletter_html(articles, config, theme_of_week=theme_of_week)
    
    # Save newsletter
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"newsletter_{datetime.now().strftime('%Y-%m-%d')}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return render_template_string(RESULT_TEMPLATE)


@app.route('/preview')
@requires_auth
def preview():
    """Preview the generated newsletter."""
    output_file = OUTPUT_DIR / f"newsletter_{datetime.now().strftime('%Y-%m-%d')}.html"
    if output_file.exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "No newsletter generated yet."


@app.route('/health')
def health():
    """Health check endpoint (no auth required)."""
    return jsonify({
        "status": "ok",
        "auth_configured": bool(AUTH_PASSWORD),
        "auth_password_length": len(AUTH_PASSWORD) if AUTH_PASSWORD else 0
    })


def open_browser():
    webbrowser.open('http://127.0.0.1:5000')


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("🤖 AI Newsletter Bot - Web Interface")
    print("=" * 50)
    
    # Check if running locally (not on cloud)
    port = int(os.environ.get('PORT', 5000))
    is_local = port == 5000 and not os.environ.get('RENDER')
    
    if is_local:
        print(f"\n🌐 Opening browser at http://127.0.0.1:{port}\n")
        Timer(1.5, open_browser).start()
    else:
        print(f"\n🌐 Running on port {port}\n")
    
    # Run Flask
    app.run(debug=False, host='0.0.0.0', port=port)
