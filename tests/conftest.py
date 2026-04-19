import sys
import os
from pathlib import Path
import pytest
import subprocess
import time
import requests

# Configure the environment
os.environ["ANIWORLD_DOWNLOAD_PATH"] = str(Path.home() / "Downloads" / "aniworld_test")
os.environ["ANIWORLD_DEBUG_MODE"] = "0"
# Ensure the src directory is in PYTHONPATH
sys.path.insert(0, os.path.abspath("/root/.openclaw/workspace/agents/klaus/AniWorld-Downloader/src"))

@pytest.fixture(scope="session", autouse=True)
def server():
    """Starts the AniWorld web server in the background for the duration of the test session."""
    # Command to start the server
    # We use the absolute path to python3 and the module aniworld
    cmd = [sys.executable, "-m", "aniworld", "--web-ui"]
    
    # Set PYTHONPATH explicitly for the subprocess
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath("/root/.openclaw/workspace/agents/klaus/AniWorld-Downloader/src")
    
    # Start the process
    # Use a more reliable way to capture logs
    log_path = "server_test.log"
    with open(log_path, "w") as log_file:
        process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=log_file,
            env=env,
            cwd="/root/.openclaw/workspace/agents/klaus/AniWorld-Downloader",
            bufsize=1 # Line buffered
        )
    
    # Wait for the server to be ready
    max_retries = 20
    ready = False
    for i in range(max_retries):
        try:
            requests.get("http://127.0.0.1:8080", timeout=1)
            ready = True
            break
        except requests.RequestException:
            time.sleep(1)
    
    if not ready:
        # If it didn't start, capture the log before failing
        with open(log_path, "r") as f:
            print(f"Server failed to start. Logs: {f.read()}")
        process.terminate()
        pytest.fail("AniWorld server failed to start on port 8080")

    yield process
    
    # Teardown: kill the server
    process.terminate()
    process.wait()

@pytest.fixture
def api_base_url():
    return "http://127.0.0.1:8080"
