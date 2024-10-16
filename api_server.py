import flask
import redis
import uuid
import json
import time
import ssl
import handlers
import config
import secrets
from flask_cors import CORS
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = flask.Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)

def simulation_traffic_middleware(request):
    if request.headers.get('X-Simulation-Traffic') == 'true':
        print("Simulated traffic detected")

@app.before_request
def before_request():
    simulation_traffic_middleware(flask.request)

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

@app.route('/ping', methods=['POST', 'GET'])
def ping():
    return flask.jsonify({"message": "ok"}), 200

@app.route('/register', methods=['POST'])
def register():
    try:
        data = flask.request.get_json()
        username, password = data.get('username'), data.get('password')
        if not all([username, password]):
            return flask.jsonify({"error": "Missing required parameters"}), 400
        if redis_client.hget(config.REDHASH_ACCOUNTS, username):
            return flask.jsonify({"error": "Username already exists"}), 409
        user_data = {
            "username": username,
            "password": generate_password_hash(password),
            "created_on": int(time.time()),
            "stars": 0,
            "total_ratings": 0
        }
        redis_client.hset(config.REDHASH_ACCOUNTS, username, json.dumps(user_data))
        return flask.jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = flask.request.get_json()
        username, password = data.get('username'), data.get('password')
        if not all([username, password]):
            return flask.jsonify({"error": "Missing required parameters"}), 400
        user_data = redis_client.hget(config.REDHASH_ACCOUNTS, username)
        if user_data:
            user = json.loads(user_data)
            if check_password_hash(user['password'], password):
                token = secrets.token_hex(32)
                redis_client.setex(f"auth_token:{token}", 3600, username)
                return flask.jsonify({"access_token": token}), 200
        return flask.jsonify({"error": "Invalid username or password"}), 401
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/account_data', methods=['GET'])
@token_required
def account_data(current_user):
    account_json = redis_client.hget(config.REDHASH_ACCOUNTS, current_user)
    if not account_json:
        return flask.jsonify({"error": "Account not found"}), 404
    account = json.loads(account_json)
    return flask.jsonify({
        "created_on": account.get("created_on", 0),
        "stars": account.get("stars", 0),
        "total_ratings": account.get("total_ratings", 0)
    }), 200

@app.route('/make_bid', methods=['POST'])
@token_required
def make_bid(current_user):
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
        data['username'] = current_user
        response, status = handlers.submit_bid(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/nearby', methods=['POST'])
@token_required
def nearby_activity(current_user):
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
        data['username'] = current_user
        response, status = handlers.nearby_activity(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/grab_job', methods=['POST'])
@token_required
def grab_job(current_user):
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
        data['username'] = current_user
        response, status = handlers.grab_job(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/sign_job', methods=['POST'])
@token_required
def sign_job(current_user):
    try:
        data = flask.request.get_json()
        if not data:
            return flask.jsonify({"error": "Invalid JSON data"}), 400
        data['username'] = current_user
        response, status = handlers.sign_job(data)
        return flask.jsonify(response), status
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.API_PORT, debug=True)

application = app
