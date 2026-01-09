"""
Article caching module with TTL (Time-To-Live) support.

Caches fetched articles to avoid redundant API calls within a time window.
"""

import json
import logging
import time
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class ArticleCache:
    """Simple file-based cache for articles with TTL support."""

    def __init__(self, cache_dir: Optional[Path] = None, ttl_seconds: int = 1800):
        """
        Initialize article cache.

        Args:
            cache_dir: Directory to store cache files (default: output/cache)
            ttl_seconds: Cache time-to-live in seconds (default 30 minutes)
        """
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / "output" / "cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl_seconds
        logger.debug(f"Cache initialized at {self.cache_dir} with TTL {ttl_seconds}s")

    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for a key."""
        # Sanitize key for filename
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Optional[dict]:
        """
        Get cached value if it exists and hasn't expired.

        Args:
            key: Cache key

        Returns:
            Cached data or None if expired/not found
        """
        cache_file = self._get_cache_file(key)

        if not cache_file.exists():
            logger.debug(f"Cache miss for key: {key}")
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Check if expired
            created_at = cache_data.get('created_at', 0)
            if time.time() - created_at > self.ttl:
                logger.debug(f"Cache expired for key: {key}")
                cache_file.unlink()  # Delete expired cache
                return None

            logger.debug(f"Cache hit for key: {key}")
            return cache_data.get('data')

        except Exception as e:
            logger.warning(f"Error reading cache for {key}: {e}")
            return None

    def set(self, key: str, value: dict) -> bool:
        """
        Set cache value with TTL.

        Args:
            key: Cache key
            value: Data to cache

        Returns:
            True if successful
        """
        cache_file = self._get_cache_file(key)

        try:
            cache_data = {
                'created_at': time.time(),
                'data': value
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)

            logger.debug(f"Cache set for key: {key}")
            return True

        except Exception as e:
            logger.warning(f"Error writing cache for {key}: {e}")
            return False

    def clear(self) -> bool:
        """
        Clear all cache files.

        Returns:
            True if successful
        """
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
            return False

    def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries.

        Returns:
            Number of expired entries removed
        """
        removed = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)

                    created_at = cache_data.get('created_at', 0)
                    if time.time() - created_at > self.ttl:
                        cache_file.unlink()
                        removed += 1

                except Exception:
                    pass

            if removed > 0:
                logger.info(f"Cleaned up {removed} expired cache entries")
            return removed

        except Exception as e:
            logger.warning(f"Error cleaning up cache: {e}")
            return 0


# Global cache instance
_cache: Optional[ArticleCache] = None


def get_cache(ttl_seconds: int = 1800) -> ArticleCache:
    """Get or create global cache instance."""
    global _cache
    if _cache is None:
        _cache = ArticleCache(ttl_seconds=ttl_seconds)
    return _cache


def cache_articles(articles: List, cache_key: str = "articles") -> bool:
    """
    Cache a list of articles.

    Args:
        articles: List of Article objects
        cache_key: Cache key name

    Returns:
        True if successful
    """
    cache = get_cache()
    # Convert articles to dicts for JSON serialization
    articles_data = [a.to_dict() if hasattr(a, 'to_dict') else a for a in articles]
    return cache.set(cache_key, {'articles': articles_data, 'count': len(articles)})


def get_cached_articles(cache_key: str = "articles") -> Optional[List]:
    """
    Get cached articles.

    Args:
        cache_key: Cache key name

    Returns:
        List of cached articles or None
    """
    cache = get_cache()
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data.get('articles', [])
    return None
