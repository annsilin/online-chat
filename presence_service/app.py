from flask import Flask, request, jsonify
from flask_cors import CORS
from .database import init_db, update_presence, get_presence
from .outbox import save_event, publish_event
import logging
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init_db()

@app.route('/presence/<user_id>', methods=['POST'])
def set_presence(user_id):
    data = request.get_json()
    status = data.get('status')
    if not status or status not in ['online', 'offline']:
        return jsonify({'error': 'Invalid status, must be online or offline'}), 400
    try:
        update_presence(user_id, status)
        event = {
            'event_id': str(uuid.uuid4()),
            'event_type': 'UserStatusChanged',
            'user_id': user_id,
            'status': status,
            'updated_at': datetime.utcnow().isoformat()
        }
        save_event(event['event_id'], event['event_type'], event)
        publish_event(event)
        return jsonify({'user_id': user_id, 'status': status}), 200
    except Exception as e:
        logger.error(f"Error setting presence for {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/presence/<user_id>', methods=['GET'])
def get_presence_route(user_id):
    try:
        presence = get_presence(user_id)
        if not presence:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(presence), 200
    except Exception as e:
        logger.error(f"Error retrieving presence for {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/presence/<user_id>', methods=['DELETE'])
def remove_presence(user_id):
    try:
        presence = get_presence(user_id)
        if not presence:
            return jsonify({'error': 'User not found'}), 404
        update_presence(user_id, 'offline')
        event = {
            'event_id': str(uuid.uuid4()),
            'event_type': 'UserStatusChanged',
            'user_id': user_id,
            'status': 'offline',
            'updated_at': datetime.utcnow().isoformat()
        }
        save_event(event['event_id'], event['event_type'], event)
        publish_event(event)
        logger.info(f"User {user_id} set to offline")
        return jsonify({'user_id': user_id, 'status': 'offline'}), 200
    except Exception as e:
        logger.error(f"Error removing presence for {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=False)