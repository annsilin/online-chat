from flask import Flask, request, jsonify
from flask_cors import CORS
from chat_service.database import init_db, insert_room, insert_message, get_room_messages, get_room_by_name
from chat_service.outbox import save_event, publish_event
from shared.config import RABBITMQ_HOST
import uuid
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

init_db()

@app.route('/rooms', methods=['POST'])
def create_room():
    data = request.get_json()
    name = data.get('name', '').strip()
    name = ''.join(c for c in name if c.isprintable())
    if not name:
        return jsonify({'error': 'Room name cannot be empty or contain invalid characters'}), 400
    created_at = datetime.utcnow().isoformat()

    # Check if room with this name already exists
    existing_room = get_room_by_name(name)
    if existing_room:
        room_id, created_at = existing_room
        logger.info(f"Reusing existing room: {name}, ID: {room_id}")
        return jsonify({'room_id': room_id, 'name': name}), 200

    # Create new room if it doesn't exist
    room_id = str(uuid.uuid4())
    try:
        logger.info(f"Creating new room: {name}, ID: {room_id}")
        insert_room(room_id, name, created_at)
        logger.info(f"Room inserted into database: {room_id}")
        event = {
            'event_id': str(uuid.uuid4()),
            'event_type': 'RoomCreated',
            'room_id': room_id,
            'name': name,
            'created_at': created_at
        }
        logger.info(f"Saving event: {event}")
        save_event(event['event_id'], event['event_type'], event)
        logger.info(f"Event saved to outbox: {event['event_id']}")
        publish_event(event)
        logger.info(f"Event published: {event}")
    except Exception as e:
        logger.error(f"Error in create_room: {str(e)}")
        return jsonify({'error': str(e)}), 500

    return jsonify({'room_id': room_id, 'name': name}), 201

@app.route('/rooms/<room_id>/messages', methods=['POST'])
def send_message(room_id):
    data = request.get_json()
    message_id = str(uuid.uuid4())
    user_id = data.get('user_id') or str(uuid.uuid4())
    content = data.get('content')
    created_at = datetime.utcnow().isoformat()

    logger.info(f"Received message for room {room_id}: user_id={user_id}, content={content}")
    try:
        insert_message(message_id, room_id, user_id, content, created_at)
        logger.info(f"Message saved: {message_id}")
        event = {
            'event_id': str(uuid.uuid4()),
            'event_type': 'MessageSent',
            'message_id': message_id,
            'room_id': room_id,
            'user_id': user_id,
            'content': content,
            'created_at': created_at
        }
        save_event(event['event_id'], event['event_type'], event)
        logger.info(f"Published event: {event}")
        publish_event(event)
    except Exception as e:
        logger.error(f"Error saving message: {str(e)}")
        return jsonify({'error': str(e)}), 500

    return jsonify({'message_id': message_id, 'user_id': user_id}), 201

@app.route('/rooms/<room_id>/messages', methods=['GET'])
def get_messages(room_id):
    messages = get_room_messages(room_id)
    logger.info(f"Fetched messages for room {room_id}: {messages}")
    return jsonify(messages), 200

if __name__ == '__main__':
    app.run(port=5003, debug=True)