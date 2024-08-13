import uuid
import redis
import json
import math

redis = redis.StrictRedis()

def calculate_distance(point1, point2):
    return math.sqrt(sum((p1 - p2) ** 2 for p1, p2 in zip(point1, point2)))

def is_bid_matching(bid, robot_data):
    if bid.get('service') not in robot_data.get('services', []):
        return False

    bid_location = (bid.get('lat', 0), bid.get('lon', 0))
    robot_location = (robot_data.get('lat', 0), robot_data.get('lon', 0))

    return calculate_distance(bid_location, robot_location) < robot_data.get("max_distance", 1)

def grab_job(robot_data):
    matched_bids = []
    for bid_id, bid_json in redis.hscan_iter("REDHASH_ALL_LIVE_BIDS"):
        bid = json.loads(bid_json)
        if is_bid_matching(bid, robot_data):
            matched_bids.append((bid.get('price', 0), bid_id, bid))

    if not matched_bids:
        return None, 204

    best_match = max(matched_bids, key=lambda x: x[0])
    _, bid_id, job = best_match

    job_id = str(uuid.uuid4())
    new_job = {
        'job_id': job_id,
        'bid_id': bid_id,
        'status': 'won',
        'job_request': robot_data,
        'bid_params': job,
    }

    redis.hset("REDHASH_ALL_WINS", bid_id, json.dumps(new_job))
    redis.hdel("REDHASH_ALL_LIVE_BIDS", bid_id)

    return new_job, 200

def has_sufficient_funds(data):
    account_id = data.get("account_id")
    bid_price = data.get("bid_price", 0)
    account_json = redis.hget("REDHASH_ACCOUNTS", account_id)
    
    if not account_json or not bid_price:
        return False

    account = json.loads(account_json)
    balance = account.get("balance", 0)

    all_outstanding = []
    for _, b in redis.hscan_iter("REDHASH_ALL_LIVE_BIDS"):
        b = json.loads(b)
        if b.get("bidder_account_id") == account_id:
            all_outstanding.append(b)

    total_outstanding = sum(b.get("bid_price", 0) for b in all_outstanding)
    
    return balance - total_outstanding - bid_price >= 0  # Changed to >= and subtracted bid_price

def submit_bid(data):
    if not has_sufficient_funds(data):
        return "", 403  # Changed to return empty string and 403 status code

    bid = data.get('bid', {})
    bid_id = str(uuid.uuid4())
    redis.hset("REDHASH_ALL_LIVE_BIDS", bid_id, json.dumps(bid))
    return bid_id, 200

def get_nearby_activity():
    all_live_bids = redis.hgetall("REDHASH_ALL_LIVE_BIDS")
    return json.dumps(all_live_bids), 200

if __name__ == "__main__":
    print("This is the main module. Run tests.py to execute the tests.")
