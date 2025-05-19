import sqlite3
import json
import pika
from shared.config import RABBITMQ_HOST

def save_event(event_id, event_type, event):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO outbox (id, event_type, payload, published) VALUES (?, ?, ?, ?)",
              (event_id, event_type, json.dumps(event), 0))
    conn.commit()
    conn.close()

def publish_event(event):
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue='chat_events')
    channel.basic_publish(exchange='',
                         routing_key='chat_events',
                         body=json.dumps(event))
    connection.close()