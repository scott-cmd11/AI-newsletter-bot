import unittest
import sys
from pathlib import Path
from flask import session

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from web import app

class TestWebCSRF(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.secret_key = 'test-secret'

        # Add a test route for CSRF verification
        @app.route('/test_csrf', methods=['POST'])
        def test_csrf():
            return "OK", 200

    def setUp(self):
        self.client = app.test_client()

    def test_csrf_missing_token(self):
        """Test that POST request without token fails with 403."""
        # Create a session with a token
        with self.client.session_transaction() as sess:
            sess['csrf_token'] = 'real-token'

        response = self.client.post('/test_csrf', data={})
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"CSRF token missing", response.data)

    def test_csrf_invalid_token(self):
        """Test that POST request with invalid token fails with 403."""
        with self.client.session_transaction() as sess:
            sess['csrf_token'] = 'real-token'

        response = self.client.post('/test_csrf', data={'csrf_token': 'fake-token'})
        self.assertEqual(response.status_code, 403)

    def test_csrf_valid_token_form(self):
        """Test that POST request with valid token in form succeeds."""
        with self.client.session_transaction() as sess:
            sess['csrf_token'] = 'real-token'

        response = self.client.post('/test_csrf', data={'csrf_token': 'real-token'})
        self.assertEqual(response.status_code, 200)

    def test_csrf_valid_token_header(self):
        """Test that POST request with valid token in header succeeds."""
        with self.client.session_transaction() as sess:
            sess['csrf_token'] = 'real-token'

        response = self.client.post('/test_csrf', headers={'X-CSRFToken': 'real-token'})
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
