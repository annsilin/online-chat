import sqlite3

def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rooms
                 (id TEXT PRIMARY KEY, name TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id TEXT PRIMARY KEY, room_id TEXT, user_id TEXT, content TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS outbox
                 (id TEXT PRIMARY KEY, event_type TEXT, payload TEXT, published INTEGER)''')
    conn.commit()
    conn.close()

def insert_room(room_id, name, created_at):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO rooms (id, name, created_at) VALUES (?, ?, ?)",
              (room_id, name, created_at))
    conn.commit()
    conn.close()

def insert_message(message_id, room_id, user_id, content, created_at):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (id, room_id, user_id, content, created_at) VALUES (?, ?, ?, ?, ?)",
              (message_id, room_id, user_id, content, created_at))
    conn.commit()
    conn.close()

def get_room_messages(room_id):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT id, user_id, content, created_at FROM messages WHERE room_id = ?", (room_id,))
    messages = [{'id': row[0], 'user_id': row[1], 'content': row[2], 'created_at': row[3]} for row in c.fetchall()]
    conn.close()
    return messages