from flask import Flask, request, jsonify
import json, uuid, redis
import handlers
import config

app = Flask(__name__)

redis=redis.StrictRedis()

@app.route('/ping', methods=['POST','GET'])
def ping():
    return '{"message" : "ok"}', 200 

##### BOTH BUYER AND SELLER INTERFACE #######
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user_type = data.get('user_type')
    
    # Add logic to store user in Redis
    user_data = {
        "password": password,
        "user_type": user_type,
        "balance": 1000  # Starting balance
    }
    redis.hset(config.REDHASH_ACCOUNTS, username, json.dumps(user_data))
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user_data = redis.hget(config.REDHASH_ACCOUNTS, username)
    if user_data:
        user = json.loads(user_data)
        if user['password'] == password:
            return jsonify({"access_token": "fake_token_for_testing"}), 200
    return jsonify({"message": "Invalid username or password"}), 401

@app.route('/account_balance', methods=['GET'])
def account_balance():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400

    account_json = redis.hget(config.REDHASH_ACCOUNTS, username)
    if not account_json:
        return jsonify({"error": "Account not found"}), 404

    account = json.loads(account_json)
    return jsonify({"balance": account.get("balance", 0)}), 200

##### BUYER INTERFACE #####
@app.route('/make_bid', methods=['POST'])
def make_bid():
    # route for buyers to submit bids
    data = request.get_json()
    response, status = handlers.submit_bid(data)
    return jsonify(response), status 

@app.route('/nearby', methods=['POST'])
def nearby_activity():
    # route for buyers to see recent nearby bids 
    data = request.get_json()
    response, status = handlers.nearby_activity(data)
    return jsonify(response), status

##### SELLER INTERFACE ###### 

@app.route('/grab_job', methods=['POST'])
def grab_job():
    # route for robots to grab jobs
    data = request.get_json()
    response, status = handlers.grab_job(data)
    return jsonify(response), status

if __name__ == '__main__':
    app.run(debug=True, port=config.API_PORT)
