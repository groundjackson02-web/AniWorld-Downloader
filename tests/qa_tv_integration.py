
import os
import sqlite3
import shutil
import tempfile
import time
from pathlib import Path
from flask import Flask
from aniworld.web.app import create_app
from aniworld.web.auth import get_current_user
from aniworld.web.db import init_db, create_user, update_playback, get_playback, get_db

# Setup a temporary directory for downloads to test library scanning
TEMP_DOWNLOAD_DIR = Path(tempfile.mkdtemp())
os.environ["ANIWORLD_DOWNLOAD_PATH"] = str(TEMP_DOWNLOAD_DIR)
os.environ["ANIWORLD_DEBUG_MODE"] = "1"

def setup_mock_library():
    """Creates a mock directory structure for testing library endpoints."""
    # Create a series folder
    series_name = "Test Series"
    series_folder = TEMP_DOWNLOAD_DIR / series_name
    series_folder.mkdir(parents=True, exist_ok=True)
    
    # Create a season folder and some episodes
    season_folder = series_folder / "Season 1"
    season_folder.mkdir(parents=True, exist_ok=True)
    
    # Mock files: S01E01, S01E02
    (season_folder / "Test Series - S01E01.mkv").touch()
    (season_folder / "Test Series - S01E02.mkv").touch()
    (season_folder / "Test Series - S01E03.mkv").touch()

def test_auth(client, api_key):
    print("Testing API Key Authentication...")
    
    # Valid Token
    with client.session_transaction() as sess:
        sess.clear()
    resp = client.get("/api/playback/recent", headers={"Authorization": f"Bearer {api_key}"})
    assert resp.status_code == 200, f"Valid token failed: {resp.status_code}"
    print("  [PASS] Valid token")

    # Invalid Token
    with client.session_transaction() as sess:
        sess.clear()
    resp = client.get("/api/playback/recent", headers={"Authorization": "Bearer invalid_token"})
    assert resp.status_code == 401, f"Invalid token should be 401: {resp.status_code}"
    print("  [PASS] Invalid token")

    # Missing Token
    with client.session_transaction() as sess:
        sess.clear()
    resp = client.get("/api/playback/recent")
    assert resp.status_code == 401, f"Missing token should be 401: {resp.status_code}"
    print("  [PASS] Missing token")


def test_tv_endpoints(client, api_key):
    print("Testing TV-Optimized Endpoints...")
    headers = {"Authorization": f"Bearer {api_key}"}

    # /api/playback/recent
    resp = client.get("/api/playback/recent", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list), "Recent playback should be a list"
    print("  [PASS] /api/playback/recent structure")

    # /api/library?view=grid
    resp = client.get("/api/library?view=grid", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "series" in data, "Grid view should have 'series' key"
    assert isinstance(data["series"], list), "Grid view series should be a list"
    print("  [PASS] /api/library?view=grid flattened structure")

    # /api/episodes/next
    resp = client.get("/api/episodes/next?url=https://aniworld.to/anime/stream/test", headers=headers)
    assert resp.status_code in (404, 500)
    print("  [PASS] /api/episodes/next error handling")

    # /api/library/recent
    resp = client.get("/api/library/recent", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict), "Recent library should be a grouped dict"
    print("  [PASS] /api/library/recent scanning")

def test_user_journey(client, api_key):
    print("Simulating User Journey...")
    headers = {"Authorization": f"Bearer {api_key}"}

    # 1. Dashboard
    resp = client.get("/api/dashboard", headers=headers)
    assert resp.status_code == 200
    assert "popular" in resp.get_json()
    print("  [PASS] Fetch Dashboard")

    # 2. Update Playback
    payload = {
        "series_url": "https://aniworld.to/anime/stream/test",
        "episode_url": "https://aniworld.to/anime/stream/test/e1",
        "timestamp": 120.5
    }
    resp = client.post("/api/playback/update", json=payload, headers=headers)
    assert resp.status_code == 200
    print("  [PASS] Update Playback")

    # 3. Get Playback (Verify update)
    resp = client.get("/api/playback/get?episode_url=https://aniworld.to/anime/stream/test/e1", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["timestamp"] == 120.5
    print("  [PASS] Get Playback")

def test_performance(client, api_key):
    print("Testing Performance (Disk Scan)...")
    headers = {"Authorization": f"Bearer {api_key}"}
    
    stress_dir = TEMP_DOWNLOAD_DIR / "stress_test"
    stress_dir.mkdir(exist_ok=True)
    for i in range(100):
        f = stress_dir / f"Series_{i}"
        f.mkdir(exist_ok=True)
        (f / "S01E01.mkv").touch()

    start = time.time()
    client.get("/api/library", headers=headers)
    end = time.time()
    duration = end - start
    print(f"  [INFO] /api/library scan time (100 series): {duration:.4f}s")
    
    if duration > 2.0:
        print("  [WARN] Performance bottleneck detected in /api/library")
    else:
        print("  [PASS] /api/library performance acceptable")

if __name__ == "__main__":
    # Wipe DB for clean QA run
    from aniworld.web.db import DB_PATH
    if DB_PATH.exists():
        DB_PATH.unlink()

    app = create_app(auth_enabled=True)
    client = app.test_client()

    
    with app.app_context():
        init_db()
        uid = create_user("qa_user", "password123", role="admin")
        
        test_api_key = "test_api_key_12345"
        conn = get_db()
        try:
            conn.execute("UPDATE users SET api_key = ? WHERE id = ?", (test_api_key, uid))
            conn.commit()
        finally:
            conn.close()
        
        key = test_api_key
    
    setup_mock_library()
    
    try:
        test_auth(client, key)
        test_tv_endpoints(client, key)
        test_user_journey(client, key)
        test_performance(client, key)
        print("\nALL QA TESTS PASSED")
    except Exception as e:
        print(f"\nQA TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    finally:
        shutil.rmtree(TEMP_DOWNLOAD_DIR)
