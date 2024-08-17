from flask import Flask, request, jsonify
import json
import redis
import uuid
import datetime
from functools import wraps
import handlers
import config

app = Flask(__name__)
redis_client = redis.StrictRedis()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        username = redis_client.get(f"auth_token:{token}")
        if not username:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        return f(username.decode(), *args, **kwargs)
    return decorated

@app.route('/ping', methods=['POST', 'GET'])
def ping():
    return jsonify({"message": "ok"}), 200 

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user_type = data.get('user_type')
    
    if not all([username, password, user_type]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    user_data = {
        "password": password,
        "user_type": user_type,
        "balance": 1000  # Starting balance
    }
    redis_client.hset(config.REDHASH_ACCOUNTS, username, json.dumps(user_data))
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not all([username, password]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    user_data = redis_client.hget(config.REDHASH_ACCOUNTS, username)
    if user_data:
        user = json.loads(user_data)
        if user['password'] == password:
            token = str(uuid.uuid4())
            redis_client.setex(f"auth_token:{token}", 3600, username)  # Expire after 1 hour
            return jsonify({"access_token": token}), 200
    return jsonify({"error": "Invalid username or password"}), 401

@app.route('/account_balance', methods=['GET'])
@token_required
def account_balance(current_user):
    account_json = redis_client.hget(config.REDHASH_ACCOUNTS, current_user)
    if not account_json:
        return jsonify({"error": "Account not found"}), 404
    account = json.loads(account_json)
    return jsonify({"balance": account.get("balance", 0)}), 200

@app.route('/make_bid', methods=['POST'])
@token_required
def make_bid(current_user):
    data = request.get_json()
    data['username'] = current_user
    response, status = handlers.submit_bid(data)
    return jsonify(response), status 

@app.route('/nearby', methods=['POST'])
@token_required
def nearby_activity(current_user):
    data = request.get_json()
    data['username'] = current_user
    response, status = handlers.nearby_activity(data)
    return jsonify(response), status

@app.route('/grab_job', methods=['POST'])
@token_required
def grab_job(current_user):
    data = request.get_json()
    data['username'] = current_user
    response, status = handlers.grab_job(data)
    return jsonify(response), status

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.API_PORT, debug=True)