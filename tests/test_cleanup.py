import pytest
import requests
import os
import time
from pathlib import Path
from datetime import datetime, timedelta

def test_cleanup_worker(api_base_url):
    """
    Verify that the auto-cleanup worker logic functions.
    Instead of relying on the background thread, we'll import and call
    the function directly to verify the logic.
    """
    from aniworld.web.app import _cleanup_worker
    import threading
    
    test_dir = Path(os.environ.get("ANIWORLD_DOWNLOAD_PATH", Path.home() / "Downloads" / "aniworld_test"))
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a new file (should NOT be deleted)
    new_file = test_dir / "new_file.txt"
    new_file.write_text("I am new")
    
    # Create an old file (should be deleted)
    old_file = test_dir / "old_file.txt"
    old_file.write_text("I am old")
    
    # Set mtime to 25 hours ago
    past_time = (datetime.utcnow() - timedelta(hours=25)).timestamp()
    os.utime(old_file, (past_time, past_time))
    
    # We can't call _cleanup_worker() directly because it's a while True loop.
    # We can run it in a thread and then kill it, or just test the logic 
    # by mocking the loop.
    
    # Since we want to test the logic inside the while True, we can't easily.
    # Let's instead implement a test for a a modified version of the logic
    # or use a timeout.
    
    # Better approach: the worker is essentially:
    # 1. Scan roots
    # 2. If file mtime > 24h, unlink.
    # 3. rmdir empty dirs.
    
    # Let's run the worker logic once in a separate thread and terminate it.
    # This is tricky. Instead, I will implement a helper in the app.py 
    # or just mock the time.
    
    # Let's try to run it in a thread and wait for the file to disappear.
    t = threading.Thread(target=_cleanup_worker, daemon=True)
    t.start()
    
    success = False
    for _ in range(20):
        if not old_file.exists() and new_file.exists():
            success = True
            break
        time.sleep(1)
    
    # Cleanup
    if new_file.exists():
        new_file.unlink()
    if old_file.exists():
        old_file.unlink()
        
    assert success, "Cleanup worker did not delete the old file"
