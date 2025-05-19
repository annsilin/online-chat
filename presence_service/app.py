from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
from .database import init_db, update_user_status, get_user_status
from shared.config import RABBITMQ_HOST
import pika
import json
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})  # Allow requests from localhost:8000

init_db()

@app.route('/presence', methods=['POST'])
def update_presence():
    data = request.get_json()
    user_id = data.get('user_id')
    status = data.get('status')
    updated_at = datetime.utcnow().isoformat()

    update_user_status(user_id, status, updated_at)

    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue='chat_events')
    event = {
        'event_type': 'UserStatusChanged',
        'user_id': user_id,
        'status': status,
        'updated_at': updated_at
    }
    channel.basic_publish(exchange='', routing_key='chat_events', body=json.dumps(event))
    connection.close()

    return jsonify({'user_id': user_id, 'status': status}), 200

@app.route('/presence/<user_id>', methods=['GET'])
def get_presence(user_id):
    status = get_user_status(user_id)
    if status:
        return jsonify({'user_id': user_id, 'status': status}), 200
    return jsonify({'error': 'User not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)