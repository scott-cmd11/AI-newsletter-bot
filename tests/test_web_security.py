
import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from web import app

class TestWebSecurity(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = app.test_client()

    @patch('web.get_review_service')
    def test_csrf_protection(self, mock_get_service):
        """
        Test CSRF protection on /save endpoint.
        """
        # Mock the service
        mock_service = MagicMock()
        mock_service.save_selections.return_value = (True, 1)
        mock_get_service.return_value = mock_service

        # 1. Test missing CSRF token
        response = self.client.post('/save', data={
            'selected': ['test:123']
        })
        self.assertEqual(response.status_code, 403, "Should return 403 when CSRF token is missing")

        # 2. Test invalid CSRF token
        # First ensure session has a token
        with self.client.session_transaction() as sess:
            sess['csrf_token'] = 'real-token'

        response = self.client.post('/save', data={
            'selected': ['test:123'],
            'csrf_token': 'fake-token'
        })
        self.assertEqual(response.status_code, 403, "Should return 403 when CSRF token is invalid")

        # 3. Test valid CSRF token
        # Note: session persists in the client, so 'csrf_token' is still 'real-token'
        response = self.client.post('/save', data={
            'selected': ['test:123'],
            'csrf_token': 'real-token'
        })
        self.assertEqual(response.status_code, 200, "Should return 200 when CSRF token is valid")
        self.assertEqual(response.json['status'], 'ok')

if __name__ == '__main__':
    unittest.main()
