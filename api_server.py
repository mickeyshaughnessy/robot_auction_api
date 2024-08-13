from flask import Flask, request, jsonify
import json, redis, uuid
import handlers

app = Flask(__name__)
redis = redis.StrictRedis()

@app.route('/ping', methods=['POST','GET'])
def ping():
    return '{"message" : "ok"}', 200 

##### BUYER INTERFACE #######
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
    response = handlers.nearby_activity(data)
    return jsonify(response), 200

##### SELLER INTERFACE ###### 

@app.route('/grab_job', methods=['POST'])
def grab_job():
    # route for robots to grab jobs
    data = request.get_json()
    response, status = handlers.grab_job(data)
    return jsonify(response), status

if __name__ == '__main__':
    app.run(debug=True, port=5001)

