import pika
import json
from shared.config import RABBITMQ_HOST
from notification_service.database import save_notification

def start_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue='chat_events')

    def callback(ch, method, properties, body):
        event = json.loads(body)
        if event['event_type'] == 'MessageSent':
            message_id = event['message_id']
            room_id = event['room_id']
            user_id = event['user_id']
            content = event['content']
            created_at = event['created_at']
            save_notification(message_id, room_id, user_id, content, created_at)
            print(f"Notification: New message in room {room_id} from user {user_id}: {content}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='chat_events', on_message_callback=callback)
    print('Notification Service consumer started...')
    channel.start_consuming()

if __name__ == '__main__':
    start_consumer()