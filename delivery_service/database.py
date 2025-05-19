import sqlite3

def init_db():
    conn = sqlite3.connect('delivery.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS deliveries
                 (message_id TEXT, room_id TEXT, user_id TEXT, status TEXT, delivered_at TEXT,
                  PRIMARY KEY (message_id, user_id))''')
    conn.commit()
    conn.close()

def save_delivery(message_id, room_id, user_id, status, delivered_at):
    conn = sqlite3.connect('delivery.db')
    c = conn.cursor()
    c.execute("INSERT INTO deliveries (message_id, room_id, user_id, status, delivered_at) VALUES (?, ?, ?, ?, ?)",
              (message_id, room_id, user_id, status, delivered_at))
    conn.commit()
    conn.close()

def get_delivery_status(message_id):
    conn = sqlite3.connect('delivery.db')
    c = conn.cursor()
    c.execute("SELECT status FROM deliveries WHERE message_id = ?", (message_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None