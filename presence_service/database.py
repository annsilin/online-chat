import sqlite3

def init_db():
    conn = sqlite3.connect('presence.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS presence
                 (user_id TEXT PRIMARY KEY, status TEXT, updated_at TEXT)''')
    conn.commit()
    conn.close()

def update_user_status(user_id, status, updated_at):
    conn = sqlite3.connect('presence.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO presence (user_id, status, updated_at) VALUES (?, ?, ?)",
              (user_id, status, updated_at))
    conn.commit()
    conn.close()

def get_user_status(user_id):
    conn = sqlite3.connect('presence.db')
    c = conn.cursor()
    c.execute("SELECT status FROM presence WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None