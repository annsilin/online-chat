import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect('presence.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS presence 
                      (user_id TEXT PRIMARY KEY, status TEXT, updated_at TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS outbox
                      (id TEXT PRIMARY KEY, event_type TEXT, payload TEXT, published INTEGER)''')
    conn.commit()
    conn.close()
    logger.info("Presence database initialized")

def update_presence(user_id, status):
    updated_at = datetime.utcnow().isoformat()
    conn = sqlite3.connect('presence.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO presence (user_id, status, updated_at) VALUES (?, ?, ?)",
                   (user_id, status, updated_at))
    conn.commit()
    conn.close()
    logger.info(f"Presence updated for {user_id}")

def get_presence(user_id):
    conn = sqlite3.connect('presence.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, status, updated_at FROM presence WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {'user_id': result[0], 'status': result[1], 'updated_at': result[2]}
    return None
