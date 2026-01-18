import pytest
from src.web import app
from flask import session

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    # Disable auth for simpler testing or mock it?
    # Actually, we rely on auth returning 401 to distinguish from CSRF 403.
    # But checking for 403 is enough for failure cases.
    with app.test_client() as client:
        yield client

def test_csrf_token_generation(client):
    """Test that a CSRF token is generated on first request."""
    client.get('/')
    with client.session_transaction() as sess:
        assert 'csrf_token' in sess
        assert len(sess['csrf_token']) > 0

def test_csrf_protection_missing_token(client):
    """Test that POST request fails if CSRF token is missing in form."""
    client.get('/') # Initialize session
    response = client.post('/save', data={})
    assert response.status_code == 403
    assert b"Invalid CSRF token" in response.data

def test_csrf_protection_invalid_token(client):
    """Test that POST request fails if CSRF token is incorrect."""
    client.get('/') # Initialize session
    response = client.post('/save', data={'csrf_token': 'invalid-token'})
    assert response.status_code == 403
    assert b"Invalid CSRF token" in response.data

def test_csrf_protection_success(client):
    """Test that POST request succeeds (passes CSRF check) with valid token."""
    client.get('/') # Initialize session

    # Get the token from the session
    token = None
    with client.session_transaction() as sess:
        token = sess['csrf_token']

    # We expect something other than 403.
    # It might be 401 (if auth enabled), 200 (success), or 500 (logic error due to empty data).
    response = client.post('/save', data={'csrf_token': token})
    assert response.status_code != 403

def test_api_exemption(client):
    """Test that API endpoints are exempt from CSRF protection."""
    client.get('/') # Initialize session

    # /api/predictions is a POST endpoint
    response = client.post('/api/predictions', json={'articles': []})

    # Should not return 403 CSRF error
    assert response.status_code != 403
    # Should return 401 (Auth required) or 400 or 200 depending on logic, but not 403
    # It returns 400 because "articles" is empty
    assert response.status_code in [400, 401, 200]
