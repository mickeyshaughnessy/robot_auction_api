from flask import Flask, request, jsonify
import redis, uuid, json, time, ssl
from functools import wraps
import handlers, config
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['APPLICATION_ROOT'] = '/api'
redis_client = redis.StrictRedis()

def simulation_traffic_middleware(request):
    if request.headers.get('X-Simulation-Traffic') == 'true':
        print("Simulated traffic detected")

@app.before_request
def before_request():
    simulation_traffic_middleware(request)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Token is missing'}), 401
        token = auth_header.split(" ")[-1]
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
    username, password = data.get('username'), data.get('password')
    if not all([username, password]):
        return jsonify({"error": "Missing required parameters"}), 400
    user_data = {
        "username": username,
        "password": handlers.hash_password(password),
        "created_on": int(time.time()),
    }
    redis_client.hset(config.REDHASH_ACCOUNTS, username, json.dumps(user_data))
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username, password = data.get('username'), data.get('password')
    if not all([username, password]):
        return jsonify({"error": "Missing required parameters"}), 400
    user_data = redis_client.hget(config.REDHASH_ACCOUNTS, username)
    if user_data:
        user = json.loads(user_data)
        if handlers.verify_password(user['password'], password):
            token = str(uuid.uuid4())
            redis_client.setex(f"auth_token:{token}", 3600, username)
            return jsonify({"access_token": token}), 200
    return jsonify({"error": "Invalid username or password"}), 401

@app.route('/account_data', methods=['GET'])
@token_required
def account_data(current_user):
    account_json = redis_client.hget(config.REDHASH_ACCOUNTS, current_user)
    if not account_json:
        return jsonify({"error": "Account not found"}), 404
    account = json.loads(account_json)
    return jsonify({
        "created_on": account.get("created_on", 0),
        "stars": account.get("stars", 0),
    }), 200

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

@app.route('/sign_job', methods=['POST'])
@token_required
def sign_job(current_user):
    data = request.get_json()
    data['username'] = current_user
    response, status = handlers.sign_job(data)
    return jsonify(response), status


if __name__ == '__main__':
    if os.environ.get('FLASK_ENV') == 'production':
        print("Warning: Running in production mode without Gunicorn is not recommended.")
        app.run(host='0.0.0.0', port=config.API_PORT)
    else:
        print("Running in development mode")
        app.run(host='0.0.0.0', port=config.API_PORT, debug=True)

if __name__ == '__main__':
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain('cert.pem', 'key.pem')
        app.run(host='0.0.0.0', port=config.API_PORT, ssl_context=context)
    except FileNotFoundError:
        print("Warning: SSL certificates not found. Running in development mode without SSL.")
        app.run(host='0.0.0.0', port=config.API_PORT, debug=True)

# This line is for Gunicorn to find the application
application = app
