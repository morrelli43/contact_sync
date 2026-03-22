"""
Flask app to receive Square booking webhooks and trigger sync.
"""
from flask import Flask, request, jsonify
import os
import threading
from main import SyncEngine

app = Flask(__name__)

# Load config from environment
sq_token = os.getenv('SQUARE_ACCESS_TOKEN')
google_creds = os.getenv('GOOGLE_CREDENTIALS_FILE', '/app/env_files/credentials.json')
google_token = os.getenv('GOOGLE_TOKEN_FILE', '/app/env_files/token.json')

engine = SyncEngine(sq_token, google_creds, google_token)

def trigger_sync_async():
    threading.Thread(target=engine.sync_upcoming).start()

@app.route('/square-webhook', methods=['POST'])
@app.route('/webhooks/square', methods=['POST'])
def square_webhook():
    event = request.json
    # Optionally, validate event signature here
    print(f"[WEBHOOK] Received event: {event}")
    # Only trigger sync for relevant event types
    if event and event.get('type', '').startswith('booking.'):
        print(f"[WEBHOOK] Triggering booking sync for event type: {event.get('type')}")
        trigger_sync_async()
    return jsonify({'status': 'ok'})

# Catch-all for debugging wrong paths
@app.route('/<path:path>', methods=['POST', 'GET'])
def catch_all(path):
    print(f"[WEBHOOK-DEBUG] Received request on unknown path: /{path}")
    if request.is_json:
        print(f"[WEBHOOK-DEBUG] Payload: {request.json}")
    return jsonify({'status': 'ignored', 'path': path}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
