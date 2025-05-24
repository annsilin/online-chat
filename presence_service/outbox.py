import sqlite3
import json
import pika
import time
import logging
from shared.config import RABBITMQ_HOST

logger = logging.getLogger(__name__)

def save_event(event_id, event_type, event):
    conn = sqlite3.connect('presence.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO outbox (id, event_type, payload, published) VALUES (?, ?, ?, ?)",
                  (event_id, event_type, json.dumps(event), 0))
    conn.commit()
    conn.close()
    logger.info(f"Saved event to outbox: {event_id}")

def publish_event(event):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue='events')
        channel.basic_publish(exchange='', routing_key='events', body=json.dumps(event))
        connection.close()
        logger.info(f"Event published: {event}")
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")
        raise
