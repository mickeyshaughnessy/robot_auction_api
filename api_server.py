from flask import Flask, request, jsonify
import json, redis, uuid

app = Flask(__name__)
redis = redis.StrictRedis()

@app.route('/submit_bid', methods=['POST'])
def submit_bid():
    data = request.get_json()
    response, status = handlers.submit_bid(data)
    return jsonify(response), status

@app.route('/grab_job', methods=['POST'])
def grab_job():
    data = request.get_json()
    response, status = handlers.grab_job(data)
    return jsonify(response), status

if __name__ == '__main__':
    app.run(debug=True)

