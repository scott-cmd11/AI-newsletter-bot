import unittest
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.web import app

class TestCSRFProtection(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.secret_key = 'test-secret'
        self.client = app.test_client()
        # Mock AUTH_PASSWORD to bypass auth
        os.environ['AUTH_PASSWORD'] = ''

    def test_post_without_token_fails(self):
        """Test that POST request without CSRF token fails with 403."""
        response = self.client.post('/save', data={'selected': ['123']})
        self.assertEqual(response.status_code, 403)

    def test_post_with_invalid_token_fails(self):
        """Test that POST request with invalid CSRF token fails with 403."""
        with self.client.session_transaction() as sess:
            sess['csrf_token'] = 'real-token'

        response = self.client.post('/save', data={
            'selected': ['123'],
            'csrf_token': 'fake-token'
        })
        self.assertEqual(response.status_code, 403)

    def test_post_with_valid_token_succeeds_csrf_check(self):
        """Test that POST request with valid CSRF token passes CSRF check."""
        with self.client:
            # First, get the token by hitting index (or manually setting session)
            # But since we use secrets, we can just manually set it in session and form
            with self.client.session_transaction() as sess:
                sess['csrf_token'] = 'valid-token'

            # We expect 500 because the service calls inside /save will fail (not mocked),
            # but NOT 403 (which would mean CSRF check failed).
            response = self.client.post('/save', data={
                'selected': ['123'],
                'csrf_token': 'valid-token'
            })

            self.assertNotEqual(response.status_code, 403)
            # It should be 500 or 200 depending on how much we mocked.
            # In this environment without mocks for services, it will likely be 500.

    def test_post_with_valid_header_token_succeeds_csrf_check(self):
        """Test that POST request with valid CSRF token in header passes CSRF check."""
        with self.client:
            with self.client.session_transaction() as sess:
                sess['csrf_token'] = 'valid-token'

            response = self.client.post('/save',
                data={'selected': ['123']},
                headers={'X-CSRFToken': 'valid-token'}
            )

            self.assertNotEqual(response.status_code, 403)

if __name__ == '__main__':
    unittest.main()
