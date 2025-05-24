from flask import Flask, jsonify
from flask_cors import CORS
from .database import init_db, get_notifications, save_notification, mark_notification_delivered
import pika
import logging
import json
import time
from shared.config import RABBITMQ_HOST
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init_db()

def is_user_online(user_id):
    try:
        response = requests.get(f"http://presence-service:5004/presence/{user_id}", timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get('status') == 'online'
    except requests.RequestException as e:
        logger.error(f"Failed to check presence for {user_id}: {e}")
        return False  # Offline if failed

def callback(ch, method, properties, body):
    try:
        event = json.loads(body.decode())
        logger.info(f"Received event: {event}")
        if event.get('event_type') == 'MessageSent':
            sender_user_id = event['user_id']
            room_id = event['room_id']
            content = event['content']

            # Get room members
            members_url = f"http://chat-service:5003/rooms/{room_id}/members"
            recipients = []
            try:
                response = requests.get(members_url, timeout=5)
                response.raise_for_status()
                recipients = response.json()
            except requests.RequestException as e:
                logger.error(f"Failed to fetch room members for {room_id}: {e}")
                # Continue with empty recipients if the endpoint fails

            recipients = [user for user in recipients if user != sender_user_id]
            for recipient in recipients:
                if is_user_online(recipient):
                    message = f"New message from User_{sender_user_id[:4]} in room {room_id}: {content}"
                    save_notification(recipient, message)

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def start_consumer():
    while True:
        max_retries = 5
        retry_delay = 5
        for attempt in range(max_retries):
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
                channel = connection.channel()
                channel.queue_declare(queue='events')
                channel.basic_consume(queue='events', on_message_callback=callback, auto_ack=False)
                logger.info("Starting consumer...")
                channel.start_consuming()
                break
            except pika.exceptions.AMQPConnectionError as e:
                logger.error(f"Failed to connect to RabbitMQ (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached. Will retry consumer in 10 seconds...")
                    time.sleep(10)

@app.route('/notifications/<user_id>', methods=['GET'])
def get_user_notifications(user_id):
    try:
        notifications = get_notifications(user_id)
        return jsonify(notifications), 200
    except Exception as e:
        logger.error(f"Error retrieving notifications for {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/notifications/<notification_id>/delivered', methods=['POST'])
def mark_delivered(notification_id):
    try:
        mark_notification_delivered(notification_id)
        return jsonify({'message': 'Notification marked as delivered'}), 200
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as delivered: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    import threading
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
    app.run(host='0.0.0.0', port=5006, debug=False)