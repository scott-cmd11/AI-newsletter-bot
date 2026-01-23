
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sources.rss_fetcher import fetch_rss_feeds, Article

class TestRSSFetcher(unittest.TestCase):

    @patch('sources.rss_fetcher.feedparser.parse')
    def test_fetch_rss_feeds_sequential_vs_parallel(self, mock_parse):
        # Setup mock return values
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Test Article 1',
                'link': 'http://example.com/1',
                'summary': 'Summary 1',
                'published_parsed': datetime.now().timetuple()
            }
        ]
        mock_parse.return_value = mock_feed

        feeds_config = [
            {'url': 'http://feed1.com', 'name': 'Feed 1'},
            {'url': 'http://feed2.com', 'name': 'Feed 2'},
            {'url': 'http://feed3.com', 'name': 'Feed 3'}
        ]

        # Call the function
        articles = fetch_rss_feeds(feeds_config)

        # Basic assertions
        self.assertEqual(len(articles), 3)
        self.assertEqual(mock_parse.call_count, 3)

        # Verify article content (order is not guaranteed with parallel execution)
        sources = {a.source for a in articles}
        self.assertEqual(sources, {'Feed 1', 'Feed 2', 'Feed 3'})

        for article in articles:
            self.assertEqual(article.title, 'Test Article 1')

if __name__ == '__main__':
    unittest.main()
