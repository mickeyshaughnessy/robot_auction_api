import flask, redis, uuid, json, time, ssl, handlers, config
from flask_cors import CORS
from functools import wraps

app = flask.Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['APPLICATION_ROOT'] = '/api'
redis_client = redis.StrictRedis()

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
    data = flask.request.get_json()
    username, password = data.get('username'), data.get('password')
    if not all([username, password]):
        return flask.jsonify({"error": "Missing required parameters"}), 400
    user_data = {
        "username": username,
        "password": handlers.hash_password(password),
        "created_on": int(time.time()),
    }
    redis_client.hset(config.REDHASH_ACCOUNTS, username, json.dumps(user_data))
    return flask.jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = flask.request.get_json()
    username, password = data.get('username'), data.get('password')
    if not all([username, password]):
        return flask.jsonify({"error": "Missing required parameters"}), 400
    user_data = redis_client.hget(config.REDHASH_ACCOUNTS, username)
    if user_data:
        user = json.loads(user_data)
        if handlers.verify_password(user['password'], password):
            token = str(uuid.uuid4())
            redis_client.setex(f"auth_token:{token}", 3600, username)
            return flask.jsonify({"access_token": token}), 200
    return flask.jsonify({"error": "Invalid username or password"}), 401

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
    }), 200

@app.route('/make_bid', methods=['POST'])
@token_required
def make_bid(current_user):
    data = flask.request.get_json()
    data['username'] = current_user
    response, status = handlers.submit_bid(data)
    return flask.jsonify(response), status 

@app.route('/nearby', methods=['POST'])
@token_required
def nearby_activity(current_user):
    data = flask.request.get_json()
    data['username'] = current_user
    response, status = handlers.nearby_activity(data)
    return flask.jsonify(response), status

@app.route('/grab_job', methods=['POST'])
@token_required
def grab_job(current_user):
    data = flask.request.get_json()
    data['username'] = current_user
    response, status = handlers.grab_job(data)
    return flask.jsonify(response), status

@app.route('/sign_job', methods=['POST'])
@token_required
def sign_job(current_user):
    data = flask.request.get_json()
    data['username'] = current_user
    response, status = handlers.sign_job(data)
    return flask.jsonify(response), status

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.API_PORT, debug=True)

application = app
