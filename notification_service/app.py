from flask import Flask, jsonify
from flask_cors import CORS  # Import CORS
from notification_service.database import init_db, get_notifications

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})  # Allow requests from localhost:8000

init_db()

@app.route('/notifications', methods=['GET'])
def get_all_notifications():
    notifications = get_notifications()
    return jsonify(notifications), 200

if __name__ == '__main__':
    app.run(port=5006, debug=True)