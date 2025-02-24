"""
Robot Services Exchange API Server
"""

import flask, os, json, time
from flask_cors import CORS
from functools import wraps
import secrets

# Import handlers
from auth import register as auth_register, login as auth_login
from buyer import submit_bid, cancel_bid
from seller import grab_job
from account import get_account
from shared import nearby_activity, sign_job
from messaging import send_chat, get_chat
from bulletin import post_bulletin, get_bulletins
from utils import redis_client, verify_password
import config

app = flask.Flask(__name__, static_url_path='', static_folder='/home/ubuntu/RSX')
CORS(app, resources={r"/*": {"origins": "*"}})

def log_request(request, response_code):
    """Log request details to Redis"""
    try:
        log_entry = {
            'timestamp': int(time.time()),
            'method': request.method,
            'path': request.path,
            'ip': request.remote_addr,
            'status': response_code,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }
        
        # Add username if authenticated
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token = auth_header.split(" ")[-1]
            username = redis_client.get(f"auth_token:{token}")
            if username:
                log_entry['username'] = username.decode()

        # Store in Redis list with auto-expiry (7 days)
        key = f"request_log:{time.strftime('%Y-%m-%d')}"
        redis_client.rpush(key, json.dumps(log_entry))
        redis_client.expire(key, 7 * 24 * 60 * 60)  # 7 days in seconds
        
    except Exception as e:
        print(f"Logging error: {str(e)}")

@app.after_request
def after_request(response):
    """Log after each request"""
    log_request(flask.request, response.status_code)
    return response

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = flask.request.headers.get('Authorization')
        if not auth_header:
            return flask.jsonify({'error': 'Token is missing'}), 401
        token = auth_header.split(" ")[-1]
        username = redis_client.get(f"auth_token:{token}")
        if not username:
            return flask.jsonify({'error': 'Token is invalid or expired'}), 401
        return f(username.decode(), *args, **kwargs)
    return decorated

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    frontend_dir = "/home/ubuntu/RSX"
    
    if not path:
        path = 'Pages/Main/Homepage.html'
    
    path = os.path.normpath(path).lstrip('/')
    full_path = os.path.join(frontend_dir, path)
    
    if os.path.isfile(full_path):
        return flask.send_from_directory(frontend_dir, path)
    
    index_path = os.path.join(full_path, 'index.html')
    if os.path.isfile(index_path):
        return flask.send_from_directory(full_path, 'index.html')
    
    return flask.send_from_directory(frontend_dir, 'Pages/Main/Homepage.html')

@app.route('/ping', methods=['POST', 'GET'])
def ping():
    return flask.jsonify({"message": "ok"}), 200

@app.route('/register', methods=['POST'])
def register():
    try:
        data = flask.request.get_json()
        response, status = auth_register(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = flask.request.get_json()
        response, status = auth_login(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/account', methods=['GET'])
@token_required
def account_data(current_user):
    try:
        # Get query parameters
        data = flask.request.args.to_dict()
        data['username'] = current_user
        response, status = get_account(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/submit_bid', methods=['POST'])
@token_required
def make_bid(current_user):
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
        data['username'] = current_user
        response, status = submit_bid(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500
        
@app.route('/cancel_bid', methods=['POST'])
@token_required
def handle_cancel_bid(current_user):
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
        data['username'] = current_user
        response, status = cancel_bid(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/nearby', methods=['POST'])
@token_required
def nearby(current_user):
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
        data['username'] = current_user
        response, status = nearby_activity(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/grab_job', methods=['POST'])
@token_required
def handle_grab_job(current_user):
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
        data['username'] = current_user
        response, status = grab_job(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/sign_job', methods=['POST'])
@token_required
def handle_sign_job(current_user):
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
        data['username'] = current_user
        response, status = sign_job(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
@token_required
def handle_send_chat(current_user):
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
        data['username'] = current_user
        response, status = send_chat(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['GET'])
@token_required
def handle_get_chat(current_user):
    try:
        data = flask.request.get_json() or {}
        data['username'] = current_user
        response, status = get_chat(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/bulletin', methods=['POST'])
@token_required
def handle_post_bulletin(current_user):
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
        data['username'] = current_user
        response, status = post_bulletin(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/bulletin', methods=['GET'])
@token_required
def handle_get_bulletins(current_user):
    try:
        data = flask.request.args.to_dict()
        response, status = get_bulletins(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.API_PORT, debug=True)

application = app
