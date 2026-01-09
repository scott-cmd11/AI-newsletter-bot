# AI Newsletter Bot - Architecture Documentation

## Overview

The refactored architecture uses **Service-Repository Pattern** to separate concerns:
- **Services**: Business logic and orchestration
- **Repositories**: Data persistence
- **Controllers** (Flask Routes): HTTP handling and responses

This provides:
- **Testability**: Services can be tested independently
- **Reusability**: Services can be used from CLI, Web, or scripts
- **Maintainability**: Clear separation of concerns
- **Scalability**: Easy to swap implementations (e.g., database instead of files)

## Directory Structure

```
src/
├── config/              # Configuration management
│   ├── __init__.py
│   └── loader.py       # Config loading with Pydantic validation
│
├── repositories/        # Data persistence layer
│   ├── __init__.py
│   └── review_repository.py    # JSON file-based review storage
│
├── services/           # Business logic layer
│   ├── __init__.py
│   ├── article_service.py          # Fetching, scoring, categorizing
│   ├── newsletter_service.py       # Newsletter generation & formatting
│   ├── review_service.py           # High-level review operations
│   └── personalization_service.py  # Learning from historical selections
│
├── sources/            # Data fetching
│   ├── __init__.py
│   └── rss_fetcher.py
│
├── processors/         # Data processing
│   ├── scorer.py
│   └── summarizer.py
│
├── formatters/         # Output formatting
│   └── email_formatter.py
│
├── templates/          # HTML templates
│   └── web_interface.html
│
├── cache.py            # Article caching with TTL
├── logger.py           # Logging setup
├── main.py             # CLI entry point
├── cli.py              # Advanced CLI
└── web.py              # Flask web interface
```

## Core Components

### 1. Services Layer

#### ArticleService
Handles article operations:
```python
service = ArticleService(config)

# Fetch and score articles
articles = service.fetch_and_score_articles(use_cache=True)

# Categorize articles
categories = service.categorize_articles(articles)

# Get top N articles
top_articles = service.get_top_articles(articles, count=8)

# Reconstruct Article objects from dictionaries
articles = service.reconstruct_articles_from_dicts(article_dicts)
```

**Methods:**
- `fetch_and_score_articles()` - Fetch from sources and score
- `categorize_articles()` - Group articles by category
- `get_top_articles()` - Get top N by score
- `reconstruct_articles_from_dicts()` - Convert dicts to Article objects
- `get_article_by_id()` - Find specific article

#### NewsletterService
Handles newsletter generation:
```python
service = NewsletterService(config, output_dir)

# Enrich articles with AI
articles, theme = service.enrich_articles_with_ai(articles)

# Generate HTML
html = service.generate_newsletter_html(articles, theme)

# Save to file
output_file = service.save_newsletter(html)

# Read existing newsletter
html = service.read_newsletter_html(date="2024-01-15")
```

**Methods:**
- `enrich_articles_with_ai()` - Generate summaries & theme
- `generate_newsletter_html()` - Create newsletter HTML
- `save_newsletter()` - Save to file
- `read_newsletter_html()` - Load from file
- `get_newsletter_file()` - Find newsletter file

#### ReviewService
High-level review operations (orchestrates other services):
```python
service = ReviewService(config, output_dir)

# Fetch articles and create review with personalization
review = service.fetch_and_create_review(use_cache=False, apply_personalization=True)

# Load existing review
review = service.load_review()

# Save user selections
success, count = service.save_selections(selected_ids)

# Get selected articles
selected = service.get_selected_articles()

# Get review statistics
summary = service.get_review_summary()

# Clear today's review
service.clear_review()
```

**Methods:**
- `fetch_and_create_review()` - Full workflow: fetch → score → categorize → personalize
- `load_review()` - Load today's review
- `save_selections()` - Save article selections
- `get_selected_articles()` - Get selected articles
- `get_review_summary()` - Get review statistics
- `clear_review()` - Delete review data

#### PersonalizationService
Learns from historical selections to personalize article recommendations:
```python
service = PersonalizationService(output_dir)

# Analyze historical selections
profile = service.analyze_historical_selections()

# Predict selection likelihood (0-100%)
likelihood = service.predict_selection_likelihood(article)

# Get personalized recommendations
recommendations = service.get_recommended_articles(articles, count=8)

# Get auto-suggested articles
suggestions = service.get_auto_suggestions(articles, threshold=75)

# Get preference profile summary
profile_summary = service.get_preference_profile_summary()
```

**Methods:**
- `analyze_historical_selections()` - Build preference profile from past reviews
- `predict_selection_likelihood()` - Get 0-100% prediction for an article
- `boost_article_score()` - Apply personalization boost to article score
- `get_recommended_articles()` - Get articles ranked by prediction
- `get_auto_suggestions()` - Get high-confidence suggestions
- `get_preference_profile_summary()` - Get human-readable profile

**Preference Profile:**
- `source_preferences` - Dict of sources → boost multipliers (1.0-2.0x)
- `category_preferences` - Dict of categories → boost multipliers
- `keyword_preferences` - Dict of keywords → frequency scores
- `preferred_sources` - List of top 5 sources
- `preferred_categories` - List of top 5 categories
- `score_range` - (min, max) scores from selections
- `selection_rate` - Percentage of articles selected

### 2. Repository Layer

#### ReviewRepository
Manages JSON file persistence:
```python
repo = ReviewRepository(output_dir)

# Load/save reviews
review = repo.load_review(date="2024-01-15")
repo.save_review(review_data)

# Create review structure
review = repo.create_review(articles)

# Update selections
review = repo.update_selections(review, selected_ids)

# Delete review
repo.delete_review(date="2024-01-15")
```

**Methods:**
- `load_review()` - Load from JSON file
- `save_review()` - Save to JSON file
- `create_review()` - Create review structure
- `update_selections()` - Mark selected articles
- `delete_review()` - Delete review file
- `get_review_file()` - Get file path

### 3. Configuration Management

#### Config Loading
```python
from config.loader import load_config, ConfigError

try:
    config = load_config()
except ConfigError as e:
    print(f"Config error: {e}")
```

**Features:**
- Pydantic validation
- Clear error messages
- Schema validation at load time
- Type safety

### 4. Caching

#### Article Cache
```python
from cache import get_cache, cache_articles, get_cached_articles

cache = get_cache()
cache.set("articles", article_data)
cached = cache.get("articles")
cache.cleanup_expired()
```

**Features:**
- TTL-based expiration (default 30 minutes)
- File-based storage
- Automatic cleanup
- Transparent integration

## Data Flow

### Web Interface Flow

```
User Request
    ↓
Flask Route (web.py)
    ↓
Service Layer (ArticleService, ReviewService, NewsletterService)
    ↓
Repository Layer (ReviewRepository)
    ↓
JSON File Storage
```

### Example: Generate Newsletter

```
/generate route
    ↓
ReviewService.get_selected_articles()
    ↓
ArticleService.reconstruct_articles_from_dicts()
    ↓
NewsletterService.enrich_articles_with_ai()
    ↓
NewsletterService.generate_newsletter_html()
    ↓
NewsletterService.save_newsletter()
    ↓
HTML File
```

## Testing

### Unit Tests
```bash
# Test services
pytest tests/test_services.py -v

# Test repositories
pytest tests/test_config.py -v

# All tests
pytest tests/ -v --cov=src
```

**Test Coverage:**
- `test_services.py` - Service layer tests
- `test_scorer.py` - Scoring logic tests
- `test_config.py` - Configuration validation tests

## Dependencies Between Components

```
Flask Routes (web.py)
    ↓
Services (ArticleService, ReviewService, NewsletterService)
    ↓ ↓ ↓
Repository (ReviewRepository)
    ↓
Cache, Logger, Config
    ↓
Data Sources (RSS, Google Alerts)
```

## Lazy Initialization

Services are initialized lazily in `web.py`:
```python
def get_review_service() -> ReviewService:
    global _review_service
    if _review_service is None:
        config = get_config()
        _review_service = ReviewService(config, OUTPUT_DIR)
    return _review_service
```

**Benefits:**
- Only loaded when needed
- Reused across requests
- Reduces startup time
- Simplifies initialization

## Error Handling

All services include:
- Try-catch blocks with logging
- Graceful fallbacks
- Clear error messages
- Exception propagation to routes

```python
try:
    articles = service.fetch_and_score_articles()
except Exception as e:
    logger.error(f"Error: {e}")
    return redirect(url_for('index'))
```

## Extending the System

### Adding a New Service

1. Create `services/new_service.py`:
```python
class NewService:
    def __init__(self, config):
        self.config = config

    def do_something(self):
        pass
```

2. Add to `services/__init__.py`:
```python
from .new_service import NewService
```

3. Use in routes:
```python
service = NewService(get_config())
result = service.do_something()
```

### Swapping Repository Implementation

Replace `ReviewRepository` with database-backed version:
```python
class DatabaseReviewRepository:
    def load_review(self, date):
        return db.query(Review).filter_by(date=date).first()
```

Services don't need to change!

### Adding a New Data Source

1. Create fetcher in `sources/`
2. Use in `ArticleService.fetch_and_score_articles()`
3. No route changes needed!

## Performance Considerations

- **Lazy Loading**: Services loaded on first use
- **Caching**: Articles cached for 30 minutes
- **Async**: Summarization parallelized
- **Logging**: Minimal overhead in production
- **File I/O**: Minimal (one file per day)

## Security

- Password protection on all routes
- Input validation at service boundary
- No sensitive data in logs
- Safe error handling (no stack traces exposed)

## Personalization API Endpoints

### Available Routes
- `GET /api/preference-profile` - Get the learned user preference profile
- `POST /api/predictions` - Get selection predictions for specific articles
  - Request body: `{"articles": [...]}`
  - Response: `{"predictions": [{"article_id": ..., "predicted_likelihood": ...}, ...]}`
- `GET /api/recommendations` - Get top 8 recommended articles
  - Response: `{"recommendations": [...]}`
- `GET /api/auto-suggestions` - Get high-confidence suggestions (>75% match)
  - Response: `{"suggestions": [...], "count": N}`

### Preference Profile Structure
```json
{
  "source_preferences": {"Source Name": 1.5, ...},
  "category_preferences": {"governance": 1.3, ...},
  "keyword_preferences": {"artificial": 5, "canada": 3, ...},
  "score_threshold": 7.0,
  "score_range": [6.0, 10.8],
  "total_selections": 16,
  "total_available": 255,
  "selection_rate": 0.063,
  "preferred_sources": ["Artificial intelligence canada", ...],
  "preferred_categories": ["governance", "security", ...]
}
```

## Monitoring & Debugging

### Enable Debug Logging
```python
from logger import setup_logger
logger = setup_logger("newsletter_bot", level="DEBUG")
```

### Key Log Points
- Service initialization
- Article fetching
- Article scoring
- Review creation
- Selection saving
- Newsletter generation

### Health Check
```
GET /health
→ {"status": "ok", "auth_configured": true}
```

## Future Improvements

1. **Database Layer**: SQLite backend instead of JSON for better scalability
2. **Event System**: Pub-sub for article events and notifications
3. **Metrics Dashboard**: Track what articles are clicked, popular topics
4. **Webhooks**: External triggers for generation (AWS Lambda, Google Cloud Functions)
5. **Multi-user**: Support multiple users/profiles with separate preferences
6. **Web UI Enhancements**: Display personalization scores and predictions in interface
7. **A/B Testing**: Test different summarization styles and preferences learning

## Completed Improvements

- ✅ Personalization System (learns from historical selections)
- ✅ Service-Repository Pattern (clean architecture)
- ✅ Configuration Validation (Pydantic)
- ✅ Structured Logging (comprehensive logging)
- ✅ Parallel API Calls (3.2x performance)
- ✅ Article Caching (5x faster repeated runs)
- ✅ Input Validation (comprehensive checks)
- ✅ Unit Tests (68+ tests)
