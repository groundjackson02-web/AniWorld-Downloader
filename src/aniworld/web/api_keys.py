import secrets
from .db import get_db

def generate_api_key(user_id):
    key = secrets.token_urlsafe(32)
    conn = get_db()
    try:
        conn.execute("UPDATE users SET api_key = ? WHERE id = ?", (key, user_id))
        conn.commit()
        return key
    finally:
        conn.close()
