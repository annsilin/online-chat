import pika
import json
from shared.config import RABBITMQ_HOST
from delivery_service.database import save_delivery
from shared.models import publish_event
from datetime import datetime

def start_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue='chat_events')

    def callback(ch, method, properties, body):
        event = json.loads(body)
        if event['event_type'] == 'MessageSent':
            # Simulate delivery to all users in the room (in practice, fetch room users)
            message_id = event['message_id']
            room_id = event['room_id']
            user_id = event['user_id']  # For demo, deliver to sender
            status = 'delivered'
            delivered_at = datetime.utcnow().isoformat()

            save_delivery(message_id, room_id, user_id, status, delivered_at)
            delivery_event = {
                'event_id': str(uuid.uuid4()),
                'event_type': 'MessageDelivered',
                'message_id': message_id,
                'room_id': room_id,
                'user_id': user_id,
                'status': status,
                'delivered_at': delivered_at
            }
            publish_event(delivery_event, 'chat_events')
            print(f"Delivery: Message {message_id} delivered to user {user_id}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='chat_events', on_message_callback=callback)
    print('Delivery Service consumer started...')
    channel.start_consuming()

if __name__ == '__main__':
    start_consumer()