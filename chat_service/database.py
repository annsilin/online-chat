import sqlite3
import logging

logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS rooms 
                      (id TEXT PRIMARY KEY, name TEXT, created_at TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages 
                      (id TEXT PRIMARY KEY, room_id TEXT, user_id TEXT, content TEXT, created_at TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS room_members 
                      (room_id TEXT, user_id TEXT, PRIMARY KEY (room_id, user_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS outbox
                      (id TEXT PRIMARY KEY, event_type TEXT, payload TEXT, published INTEGER)''')
    conn.commit()
    conn.close()
    logger.info("Chat database initialized")

def get_room_by_name(name):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, created_at FROM rooms WHERE name = ?", (name,))
    room = cursor.fetchone()
    conn.close()
    return room  # Returns (id, created_at) tuple if found, None if not

def insert_room(room_id, name, created_at):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO rooms (id, name, created_at) VALUES (?, ?, ?)", (room_id, name, created_at))
    conn.commit()
    conn.close()

def insert_message(message_id, room_id, user_id, content, created_at):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (id, room_id, user_id, content, created_at) VALUES (?, ?, ?, ?, ?)",
                   (message_id, room_id, user_id, content, created_at))
    conn.commit()
    conn.close()

def get_messages(room_id):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, content, created_at FROM messages WHERE room_id = ? ORDER BY created_at", (room_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{'id': row[0], 'user_id': row[1], 'content': row[2], 'created_at': row[3]} for row in rows]

def insert_room_member(room_id, user_id):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO room_members (room_id, user_id) VALUES (?, ?)", (room_id, user_id))
    conn.commit()
    conn.close()

def get_room_members(room_id):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM room_members WHERE room_id = ?", (room_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows] if rows else []
