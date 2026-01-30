import pytest
from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import app after path setup
from web import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    # Ensure AUTH_PASSWORD is empty so we don't need basic auth
    with patch('web.AUTH_PASSWORD', ''):
        with app.test_client() as client:
            yield client

def test_csrf_missing_token_fails(client):
    """
    Test that a POST request without a CSRF token FAILS (403).
    """
    with patch('web.get_review_service') as mock_get_service:
        # Mock the service
        mock_service = MagicMock()
        mock_service.save_selections.return_value = (True, 1)
        mock_get_service.return_value = mock_service

        # Post without CSRF token
        response = client.post('/save', data={'selected': ['test:1']})

        # Assert FAILURE (403 Forbidden)
        assert response.status_code == 403

def test_csrf_valid_token_succeeds(client):
    """
    Test that a POST request WITH a valid CSRF token SUCCEEDS.
    """
    with patch('web.get_review_service') as mock_get_service:
        # Mock the service
        mock_service = MagicMock()
        mock_service.save_selections.return_value = (True, 1)

        # Mock load_review for the index page if needed, but we can just set session manually
        mock_get_service.return_value = mock_service

        # Manually set a token in the session
        with client.session_transaction() as sess:
            sess['csrf_token'] = 'valid-token-123'

        # Post with the matching token
        response = client.post('/save', data={
            'selected': ['test:1'],
            'csrf_token': 'valid-token-123'
        })

        assert response.status_code == 200
        assert response.json['status'] == 'ok'

def test_csrf_invalid_token_fails(client):
    """
    Test that a POST request with an INVALID CSRF token FAILS.
    """
    with patch('web.get_review_service') as mock_get_service:
        # Mock the service
        mock_service = MagicMock()
        mock_service.save_selections.return_value = (True, 1)
        mock_get_service.return_value = mock_service

        # Manually set a token in the session
        with client.session_transaction() as sess:
            sess['csrf_token'] = 'real-token'

        # Post with a WRONG token
        response = client.post('/save', data={
            'selected': ['test:1'],
            'csrf_token': 'wrong-token'
        })

        assert response.status_code == 403
