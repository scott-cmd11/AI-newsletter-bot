import time
import feedparser
from unittest.mock import MagicMock
from src.sources.rss_fetcher import fetch_rss_feeds

def mock_parse(url):
    time.sleep(0.5) # Simulate 500ms network delay
    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_feed.entries = []
    return mock_feed

# Monkey patch feedparser.parse
original_parse = feedparser.parse
feedparser.parse = mock_parse

config = [{'url': f'http://example.com/feed{i}', 'name': f'Feed {i}'} for i in range(10)]

print("Starting benchmark with 10 simulated feeds (0.5s delay each)...")
start_time = time.time()
fetch_rss_feeds(config)
end_time = time.time()

print(f"Time taken: {end_time - start_time:.2f} seconds")

# Restore
feedparser.parse = original_parse
