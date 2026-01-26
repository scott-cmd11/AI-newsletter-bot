
import unittest
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import web

class TestCSRFSecurity(unittest.TestCase):
    def setUp(self):
        self.app = web.app.test_client()
        self.app.testing = True
        web.app.config['SECRET_KEY'] = 'test-secret-key'

    def test_save_selection_without_csrf(self):
        """Test that POST request fails without CSRF token."""
        with patch('web.AUTH_PASSWORD', ''):
             # Try POST without CSRF
            response = self.app.post('/save',
                                     data={'selected': ['gov:123']})

            self.assertEqual(response.status_code, 403, "Should be forbidden (403)")

    def test_save_selection_with_csrf(self):
        """Test that POST request succeeds with CSRF token."""
        with patch('web.AUTH_PASSWORD', ''):
            with self.app.session_transaction() as sess:
                sess['csrf_token'] = 'test-token-123'

            # Since we didn't mock the service, it will 500 or fail later, but NOT 403.
            response = self.app.post('/save',
                                     data={
                                         'selected': ['gov:123'],
                                         'csrf_token': 'test-token-123'
                                     })

            self.assertNotEqual(response.status_code, 403, f"Should not be forbidden with valid token. Got {response.status_code}")

    def test_save_selection_with_header_csrf(self):
        """Test that POST request succeeds with X-CSRFToken header."""
        with patch('web.AUTH_PASSWORD', ''):
            with self.app.session_transaction() as sess:
                sess['csrf_token'] = 'test-token-header'

            response = self.app.post('/save',
                                     data={'selected': ['gov:123']},
                                     headers={'X-CSRFToken': 'test-token-header'})

            self.assertNotEqual(response.status_code, 403, f"Should not be forbidden with valid header token. Got {response.status_code}")

if __name__ == '__main__':
    unittest.main()
