from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
from .database import init_db, save_delivery, get_delivery_status
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})  # Allow requests from localhost:8000

init_db()

@app.route('/deliveries', methods=['POST'])
def save_delivery_route():
    data = request.get_json()
    message_id = data.get('message_id')
    room_id = data.get('room_id')
    user_id = data.get('user_id')
    status = data.get('status')
    delivered_at = datetime.utcnow().isoformat()

    save_delivery(message_id, room_id, user_id, status, delivered_at)
    return jsonify({'message_id': message_id, 'user_id': user_id, 'status': status}), 201

@app.route('/deliveries/<message_id>', methods=['GET'])
def get_delivery(message_id):
    status = get_delivery_status(message_id)
    if status:
        return jsonify({'message_id': message_id, 'status': status}), 200
    return jsonify({'error': 'Delivery not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)