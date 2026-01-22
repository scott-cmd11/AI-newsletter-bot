import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from web import app

class TestCSRF(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.secret_key = 'test-secret'
        self.client = app.test_client()

    def test_save_without_csrf_token(self):
        # Mock the service
        with patch('web.get_review_service') as mock_service:
            mock_service.return_value.save_selections.return_value = (True, 5)

            # Try to POST without a token
            # This should now FAIL with 403
            response = self.client.post('/save', data={'selected': ['1', '2']})

            self.assertEqual(response.status_code, 403)

    def test_save_with_csrf_token(self):
        with patch('web.get_review_service') as mock_service:
            mock_service.return_value.save_selections.return_value = (True, 5)

            # Manually set the token in the session
            with self.client.session_transaction() as sess:
                sess['csrf_token'] = 'valid-token'

            # POST with the token
            response = self.client.post('/save', data={
                'selected': ['1', '2'],
                'csrf_token': 'valid-token'
            })

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['status'], 'ok')
