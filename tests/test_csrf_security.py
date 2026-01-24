import sys
import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Mock environment variables
os.environ['AUTH_PASSWORD'] = 'testpass'
os.environ['SECRET_KEY'] = 'testsecret'

# Need to mock load_config before importing web because web imports services which import config
with patch('config.loader.load_config', return_value={}):
    from web import app

class CSRFFixTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.headers = {
            'Authorization': 'Basic dXNlcjp0ZXN0cGFzcw==' # user:testpass base64
        }

    def test_post_with_csrf_token_in_form(self):
        """Verify that POST requests with valid CSRF token in form succeed."""
        with self.client.session_transaction() as sess:
            # Generate a token in session
            sess['csrf_token'] = 'valid_token'

        with patch('web.get_review_service') as mock_service_getter:
            mock_service = MagicMock()
            mock_service.save_selections.return_value = (True, 5)
            mock_service_getter.return_value = mock_service

            # Send POST with matching token
            response = self.client.post('/save',
                data={'selected': ['1', '2'], 'csrf_token': 'valid_token'},
                headers=self.headers
            )

            self.assertEqual(response.status_code, 200)

    def test_post_with_csrf_token_in_header(self):
        """Verify that POST requests with valid CSRF token in header succeed."""
        with self.client.session_transaction() as sess:
            # Generate a token in session
            sess['csrf_token'] = 'valid_token'

        with patch('web.get_review_service') as mock_service_getter:
            mock_service = MagicMock()
            mock_service.save_selections.return_value = (True, 5)
            mock_service_getter.return_value = mock_service

            # Send POST with matching token in header
            headers = self.headers.copy()
            headers['X-CSRFToken'] = 'valid_token'

            response = self.client.post('/save',
                data={'selected': ['1', '2']},
                headers=headers
            )

            self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
