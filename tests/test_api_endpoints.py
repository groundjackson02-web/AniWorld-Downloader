import pytest
import requests

def test_api_popular(api_base_url):
    response = requests.get(f"{api_base_url}/api/popular")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_api_dashboard(api_base_url):
    response = requests.get(f"{api_base_url}/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "popular" in data
    assert "new" in data

def test_api_search_get(api_base_url):
    response = requests.get(f"{api_base_url}/api/search", params={"q": "Naruto"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_api_search_post(api_base_url):
    response = requests.post(
        f"{api_base_url}/api/search", 
        json={"keyword": "Naruto", "site": "aniworld"},
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_api_series(api_base_url):
    # We need a valid URL. Since we don't have one, we can try a known one 
    # or mock it. But the task asks to test the endpoint.
    # Let's try to get a URL from the search first.
    search_resp = requests.get(f"{api_base_url}/api/search", params={"q": "Naruto"})
    results = search_resp.json()
    if not results:
        pytest.skip("No search results found to test /api/series")
    
    url = results[0]["url"]
    response = requests.get(f"{api_base_url}/api/series", params={"url": url})
    assert response.status_code == 200
    data = response.json()
    assert "title" in data

def test_api_stream(api_base_url):
    # /api/stream/<path:file_path>
    # We need a file to exist in the download path.
    import os
    from pathlib import Path
    
    test_dir = Path(os.environ.get("ANIWORLD_DOWNLOAD_PATH", Path.home() / "Downloads" / "aniworld_test"))
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "test_video.mp4"
    test_file.write_text("dummy content")
    
    # The endpoint expects the path relative to the root
    response = requests.get(f"{api_base_url}/api/stream/test_video.mp4")
    assert response.status_code == 200
    
    # Cleanup
    test_file.unlink()
