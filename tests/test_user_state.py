import pytest
from aniworld.web.app import create_app
from aniworld.web.db import init_db, create_user

@pytest.fixture
def app():
    # Create app with auth enabled
    app = create_app(auth_enabled=True)
    
    # Setup test database
    init_db()
    # Create an admin to bypass setup page
    create_user("admin", "adminpassword123", role="admin")
    # Create test user
    create_user("testuser", "testpassword123", role="user")
    
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    # Login the test user
    # We need to handle CSRF for the login form
    resp = client.get("/login")
    import re
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', resp.data.decode())
    csrf_token = csrf_match.group(1)
    
    client.post("/login", data={
        "username": "testuser",
        "password": "testpassword123",
        "csrf_token": csrf_token
    }, follow_redirects=True)
    
    return client

def test_playback_update_and_get(auth_client):
    series_url = "https://aniworld.to/anime/stream/test-series"
    episode_url = "https://aniworld.to/anime/stream/test-episode"
    timestamp = 123.45
    
    # Update playback
    resp = auth_client.post("/api/playback/update", json={
        "series_url": series_url,
        "episode_url": episode_url,
        "timestamp": timestamp
    })
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True}
    
    # Get playback
    resp = auth_client.get(f"/api/playback/get?episode_url={episode_url}")
    assert resp.status_code == 200
    assert resp.get_json()["timestamp"] == timestamp

def test_library_management(auth_client):
    series_url = "https://aniworld.to/anime/stream/test-library-series"
    
    # Add to watchlist
    resp = auth_client.post("/api/library/update", json={
        "series_url": series_url,
        "status": "watchlist"
    })
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True}
    
    # Verify it's there
    resp = auth_client.get("/api/library/get")
    assert resp.status_code == 200
    library = resp.get_json()
    assert any(item["series_url"] == series_url and item["status"] == "watchlist" for item in library)
    
    # Remove from library
    resp = auth_client.post("/api/library/remove", json={
        "series_url": series_url
    })
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True}
    
    # Verify it's gone
    resp = auth_client.get("/api/library/get")
    assert resp.status_code == 200
    library = resp.get_json()
    assert not any(item["series_url"] == series_url for item in library)
