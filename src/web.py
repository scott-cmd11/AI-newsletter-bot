#!/usr/bin/env python3
"""
AI Newsletter Bot - Web Interface

A simple Flask web app for curating newsletter articles.
"""

import os
import json
import logging
import webbrowser
from datetime import datetime
from pathlib import Path
from threading import Timer
from functools import wraps

from flask import Flask, render_template_string, request, redirect, url_for, jsonify, Response

logger = logging.getLogger(__name__)

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from config.loader import load_config, ConfigError
from services import ArticleService, NewsletterService, ReviewService
from sources.rss_fetcher import Article

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# CSRF Protection
import secrets
from flask import session, abort

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.get('_csrf_token')
        if not token:
            app.logger.warning("CSRF attempt: No token in session")
            abort(403)

        request_token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')

        if not request_token or not secrets.compare_digest(token, request_token):
            app.logger.warning("CSRF attempt: Invalid token")
            abort(403)

# Password protection - set AUTH_PASSWORD env var in Railway
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

# Global service instances (lazy initialized)
_config = None
_review_service = None
_article_service = None
_newsletter_service = None

# Progress tracking for fetch operations
_fetch_progress = {
    "status": "idle",  # idle, fetching, analyzing, scoring, personalizing, complete
    "message": "",
    "percentage": 0
}


def get_config() -> dict:
    """Get or load config."""
    global _config
    if _config is None:
        try:
            _config = load_config()
        except ConfigError as e:
            logger.error(f"Failed to load config: {e}")
            raise
    return _config


def get_review_service() -> ReviewService:
    """Get or initialize review service."""
    global _review_service
    if _review_service is None:
        config = get_config()
        _review_service = ReviewService(config, OUTPUT_DIR)
    return _review_service


def get_article_service() -> ArticleService:
    """Get or initialize article service."""
    global _article_service
    if _article_service is None:
        config = get_config()
        _article_service = ArticleService(config, output_dir=OUTPUT_DIR)
    return _article_service


def get_newsletter_service() -> NewsletterService:
    """Get or initialize newsletter service."""
    global _newsletter_service
    if _newsletter_service is None:
        config = get_config()
        _newsletter_service = NewsletterService(config, OUTPUT_DIR)
    return _newsletter_service


def load_html_template() -> str:
    """Load HTML template from file."""
    template_path = Path(__file__).parent / "templates" / "web_interface.html"
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        # Fallback if template file not found (shouldn't happen in production)
        logger = logging.getLogger(__name__)
        logger.error(f"HTML template not found at {template_path}")
        return "<html><body><h1>Error: Template not found</h1></body></html>"


# Load HTML Template at module level
HTML_TEMPLATE = load_html_template()

# Original inline template kept for reference during migration
_ORIGINAL_TEMPLATE = '''
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
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
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
    """Display article curation interface."""
    try:
        review_service = get_review_service()
        data = review_service.load_review()

        # Get personalization data if available
        if data and 'preference_profile' not in data:
            article_service = get_article_service()
            profile = article_service.get_preference_profile()
            if profile:
                data['preference_profile'] = profile

        return render_template_string(HTML_TEMPLATE, data=data)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return render_template_string(HTML_TEMPLATE, data=None)


def update_progress(status: str, message: str, percentage: int) -> None:
    """Update fetch progress."""
    global _fetch_progress
    _fetch_progress["status"] = status
    _fetch_progress["message"] = message
    _fetch_progress["percentage"] = min(100, max(0, percentage))
    logger.debug(f"Progress: {status} - {message} ({percentage}%)")


@app.route('/api/progress')
@requires_auth
def get_progress():
    """Get current fetch progress."""
    return jsonify(_fetch_progress)


@app.route('/fetch')
@requires_auth
def fetch_articles():
    """Fetch and score new articles."""
    try:
        logger.info("Fetch articles request")
        update_progress("fetching", "Fetching articles from sources...", 10)
        review_service = get_review_service()

        # Fetch articles and create review (no personalization for speed)
        review_data = review_service.fetch_and_create_review(use_cache=False, apply_personalization=False)

        if not review_data or not review_data.get('categories'):
            logger.warning("No articles available to fetch")
            update_progress("error", "No articles available", 0)
            return redirect(url_for('index'))

        update_progress("complete", f"Fetched {review_data.get('total_articles', 0)} articles", 100)
        logger.info(f"Fetched {review_data.get('total_articles', 0)} articles")

        # Reset progress after 2 seconds
        return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Error in fetch_articles route: {e}")
        update_progress("error", f"Error: {str(e)}", 0)
        return redirect(url_for('index'))


@app.route('/save', methods=['POST'])
@requires_auth
def save_selection():
    """Save article selection."""
    try:
        logger.info("Save selection request")
        review_service = get_review_service()

        # Get selected article IDs
        selected_ids = request.form.getlist('selected')

        # Save selections
        success, count = review_service.save_selections(selected_ids)

        if success:
            logger.info(f"Saved {count} article selections")
            return jsonify({"status": "ok", "count": count})
        else:
            logger.error("Failed to save selections")
            return jsonify({"status": "error", "count": 0}), 500

    except Exception as e:
        logger.error(f"Error in save_selection route: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/generate')
@requires_auth
def generate():
    """Generate newsletter from selected articles."""
    try:
        logger.info("Generate newsletter request")
        review_service = get_review_service()
        newsletter_service = get_newsletter_service()
        article_service = get_article_service()

        # Get selected articles
        selected = review_service.get_selected_articles()
        if not selected:
            logger.warning("No articles selected for newsletter generation")
            return redirect(url_for('index'))

        logger.info(f"Generating newsletter from {len(selected)} selected articles")

        # Reconstruct Article objects
        articles = article_service.reconstruct_articles_from_dicts(selected)
        if not articles:
            logger.error("Failed to reconstruct articles")
            return redirect(url_for('index'))

        # Step 1: Enrich articles with section-specific AI summaries
        selected_sections = newsletter_service.enrich_selected_articles(articles)
        
        # Step 2: Generate "Theme of the Week" for better synthesis
        from processors.summarizer import generate_theme_of_week
        theme_of_week = generate_theme_of_week(articles, newsletter_service.config)
        
        # Step 3: Generate HTML using the section-based layout
        # (Inject theme_of_week if successfully generated)
        selected_sections['theme_of_week'] = theme_of_week if theme_of_week and theme_of_week.get('enabled') else None
        
        html = newsletter_service.generate_newsletter_html_sections(selected_sections)

        # Save newsletter
        output_file = newsletter_service.save_newsletter(html)
        logger.info(f"Newsletter saved to {output_file}")

        return render_template_string(RESULT_TEMPLATE)

    except Exception as e:
        logger.error(f"Error in generate route: {e}")
        return render_template_string(RESULT_TEMPLATE)


@app.route('/preview')
@requires_auth
def preview():
    """Preview the generated newsletter."""
    try:
        newsletter_service = get_newsletter_service()
        html_content = newsletter_service.read_newsletter_html()
        if html_content:
            return html_content
        return "<h1>No newsletter generated yet</h1>"
    except Exception as e:
        logger.error(f"Error in preview route: {e}")
        return "<h1>Error loading newsletter</h1>"


@app.route('/api/preference-profile')
@requires_auth
def get_preference_profile_api():
    """Get user preference profile from personalization."""
    try:
        article_service = get_article_service()
        profile = article_service.get_preference_profile()

        if profile:
            return jsonify({
                "status": "ok",
                "profile": profile
            })
        else:
            return jsonify({
                "status": "no_profile",
                "message": "Personalization data not available yet"
            }), 404

    except Exception as e:
        logger.error(f"Error getting preference profile: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/predictions', methods=['POST'])
@requires_auth
def get_article_predictions():
    """Get personalization predictions for articles."""
    try:
        article_service = get_article_service()

        # Get articles from request
        articles = request.json.get('articles', [])
        if not articles:
            return jsonify({
                "status": "error",
                "message": "No articles provided"
            }), 400

        predictions = []
        for article in articles:
            if article_service.personalization_service:
                likelihood = article_service.personalization_service.predict_selection_likelihood(article)
                boosted_score = article_service.personalization_service.boost_article_score(article)
                predictions.append({
                    "article_id": article.get('id'),
                    "title": article.get('title'),
                    "predicted_likelihood": likelihood,
                    "boosted_score": boosted_score,
                    "original_score": article.get('score')
                })

        return jsonify({
            "status": "ok",
            "predictions": predictions
        })

    except Exception as e:
        logger.error(f"Error getting article predictions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/recommendations')
@requires_auth
def get_recommendations():
    """Get personalized article recommendations."""
    try:
        review_service = get_review_service()
        data = review_service.load_review()

        if not data or not data.get('categories'):
            return jsonify({
                "status": "error",
                "message": "No articles available"
            }), 404

        # Get all articles from categories
        all_articles = []
        for category, articles in data.get('categories', {}).items():
            if isinstance(articles, list):
                all_articles.extend(articles)

        # Get recommendations
        article_service = get_article_service()
        recommendations = article_service.get_personalized_recommendations(
            [Article(
                title=a['title'],
                url=a['url'],
                source=a['source'],
                published=datetime.fromisoformat(a['published']) if a.get('published') else datetime.now(),
                summary=a.get('summary', ''),
                category=a.get('category', ''),
                score=a.get('score', 0.0)
            ) for a in all_articles],
            count=8
        )

        return jsonify({
            "status": "ok",
            "recommendations": recommendations
        })

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/auto-suggestions')
@requires_auth
def get_auto_suggestions():
    """Get auto-suggested articles matching user preferences."""
    try:
        review_service = get_review_service()
        data = review_service.load_review()

        if not data or not data.get('categories'):
            return jsonify({
                "status": "error",
                "message": "No articles available"
            }), 404

        # Get all articles from categories
        all_articles = []
        for category, articles in data.get('categories', {}).items():
            if isinstance(articles, list):
                all_articles.extend(articles)

        # Get suggestions
        article_service = get_article_service()
        suggestions = article_service.get_auto_suggestions(
            [Article(
                title=a['title'],
                url=a['url'],
                source=a['source'],
                published=datetime.fromisoformat(a['published']) if a.get('published') else datetime.now(),
                summary=a.get('summary', ''),
                category=a.get('category', ''),
                score=a.get('score', 0.0)
            ) for a in all_articles],
            threshold=75
        )

        return jsonify({
            "status": "ok",
            "suggestions": suggestions,
            "count": len(suggestions)
        })

    except Exception as e:
        logger.error(f"Error getting auto-suggestions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint (no auth required)."""
    return jsonify({
        "status": "ok",
        "version": "2.0"
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
