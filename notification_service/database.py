import sqlite3
import uuid


def init_db():
    conn = sqlite3.connect('notification.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS notifications
                 (id TEXT PRIMARY KEY, message_id TEXT, room_id TEXT, user_id TEXT, content TEXT, created_at TEXT)''')
    conn.commit()
    conn.close()

def save_notification(message_id, room_id, user_id, content, created_at):
    conn = sqlite3.connect('notification.db')
    c = conn.cursor()
    notification_id = str(uuid.uuid4())
    c.execute("INSERT INTO notifications (id, message_id, room_id, user_id, content, created_at) VALUES (?, ?, ?, ?, ?, ?)",
              (notification_id, message_id, room_id, user_id, content, created_at))
    conn.commit()
    conn.close()

def get_notifications():
    conn = sqlite3.connect('notification.db')
    c = conn.cursor()
    c.execute("SELECT message_id, room_id, user_id, content, created_at FROM notifications")
    notifications = [{'message_id': row[0], 'room_id': row[1], 'user_id': row[2], 'content': row[3], 'created_at': row[4]}
                    for row in c.fetchall()]
    conn.close()
    return notifications