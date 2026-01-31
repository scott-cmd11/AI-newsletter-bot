
import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path
import os
from flask import session

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from web import app

class TestCSRF(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True
        app.secret_key = 'test-secret'
        os.environ['AUTH_PASSWORD'] = 'testpass'

    def test_post_without_csrf_token_fails(self):
        """
        Verifies that a POST request without a CSRF token is rejected.
        """
        with patch('web.get_review_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.save_selections.return_value = (True, 1)
            mock_get_service.return_value = mock_service

            # Simulate an authenticated POST request without CSRF token
            response = self.client.post(
                '/save',
                data={'selected': ['tech:123']},
                headers={'Authorization': 'Basic dXNlcjp0ZXN0cGFzcw=='}
            )

            self.assertEqual(response.status_code, 403)

    def test_post_with_valid_csrf_token_succeeds(self):
        """
        Verifies that a POST request with a valid CSRF token is accepted.
        """
        with patch('web.get_review_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.save_selections.return_value = (True, 1)
            mock_get_service.return_value = mock_service

            # Manually set the token in the session
            with self.client.session_transaction() as sess:
                sess['csrf_token'] = 'valid-token'

            # Make request with the same token
            response = self.client.post(
                '/save',
                data={'selected': ['tech:123'], 'csrf_token': 'valid-token'},
                headers={'Authorization': 'Basic dXNlcjp0ZXN0cGFzcw=='}
            )

            self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
