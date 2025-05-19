import pika
import json
from shared.config import RABBITMQ_HOST

def publish_event(event, queue):
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=queue)
    channel.basic_publish(exchange='',
                         routing_key=queue,
                         body=json.dumps(event))
    connection.close()