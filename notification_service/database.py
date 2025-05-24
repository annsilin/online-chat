from datetime import datetime
import sqlite3
import logging

logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect('notifications.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS notifications 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       user_id TEXT, 
                       message TEXT, 
                       created_at TEXT, 
                       delivered BOOLEAN DEFAULT 0)''')
    conn.commit()
    conn.close()
    logger.info("Notifications database initialized")

init_db()

def save_notification(user_id, message):
    created_at = datetime.utcnow().isoformat()
    try:
        conn = sqlite3.connect('notifications.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notifications (user_id, message, created_at) VALUES (?, ?, ?)",
                       (user_id, message, created_at))
        conn.commit()
        logger.info(f"Saved notification for {user_id}: {message}")
    except sqlite3.Error as e:
        logger.error(f"Database error while saving notification for {user_id}: {e}")
        raise
    finally:
        conn.close()

def mark_notification_delivered(notification_id):
    try:
        conn = sqlite3.connect('notifications.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET delivered = 1 WHERE id = ?", (notification_id,))
        conn.commit()
        logger.info(f"Marked notification {notification_id} as delivered")
    except sqlite3.Error as e:
        logger.error(f"Database error while marking notification {notification_id} as delivered: {e}")
        raise
    finally:
        conn.close()

def get_notifications(user_id):
    try:
        conn = sqlite3.connect('notifications.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, message, created_at, delivered FROM notifications WHERE user_id = ? AND delivered = 0", (user_id,))
        results = cursor.fetchall()
        notifications = [{'id': r[0], 'user_id': r[1], 'message': r[2], 'created_at': r[3], 'delivered': bool(r[4])} for r in results]
        logger.info(f"Fetched {len(notifications)} pending notifications for {user_id}")
        return notifications
    except sqlite3.Error as e:
        logger.error(f"Database error while retrieving notifications for {user_id}: {e}")
        raise
    finally:
        conn.close()