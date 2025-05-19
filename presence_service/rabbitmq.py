import pika
import json
from shared.config import RABBITMQ_HOST

def start_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue='chat_events')

    def callback(ch, method, properties, body):
        event = json.loads(body)
        if event['event_type'] == 'UserStatusChanged':
            print(f"Presence: User {event['user_id']} is now {event['status']}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='chat_events', on_message_callback=callback)
    print('Presence Service consumer started...')
    channel.start_consuming()

if __name__ == '__main__':
    start_consumer()