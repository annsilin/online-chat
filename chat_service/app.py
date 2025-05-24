import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from .database import init_db, insert_message, get_messages, insert_room, get_room_members, insert_room_member, get_room_by_name
import uuid
import json
import pika
from datetime import datetime
import logging
from shared.config import RABBITMQ_HOST
from .outbox import save_event, publish_event

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})

logging.basicConfig(level=logging.INFO)
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
    if not content:
        return jsonify({'error': 'Missing content'}), 400
    created_at = datetime.utcnow().isoformat()
    logger.info(f"Received message for room {room_id}: user_id={user_id}, content={content}")
    try:
        insert_message(message_id, room_id, user_id, content, created_at)
        insert_room_member(room_id, user_id)
        # Register user in Presence Service with error handling
        presence_url = f"http://presence-service:5004/presence/{user_id}"
        try:
            response = requests.post(presence_url, json={'status': 'online'}, timeout=5)
            response.raise_for_status()
            logger.info(f"Registered presence for {user_id}: {response.json()}")
        except requests.RequestException as e:
            logger.error(f"Failed to register presence for {user_id}: {e}")
            # Continue without failing the message send
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
        publish_event(event)
        logger.info(f"Event published: {event}")
    except Exception as e:
        logger.error(f"Error saving message: {str(e)}")
        return jsonify({'error': str(e)}), 500
    return jsonify({'message_id': message_id, 'user_id': user_id}), 201

@app.route('/rooms/<room_id>/messages', methods=['GET'])
def get_room_messages(room_id):
    messages = get_messages(room_id)
    logger.info(f"Fetched messages for room {room_id}: {messages}")
    return jsonify(messages), 200

@app.route('/rooms/<room_id>/members', methods=['GET'])
def get_room_members_route(room_id):
    try:
        members = get_room_members(room_id)
        return jsonify(members), 200
    except Exception as e:
        logger.error(f"Error fetching members for room {room_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=False)