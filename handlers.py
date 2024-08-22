import uuid, redis, json, math, time
from config import SIMULATION_KEY, REDHASH_ALL_LIVE_BIDS, REDHASH_ALL_WINS, REDHASH_ACCOUNTS
from match import matched_service

redis_client = redis.StrictRedis()

def is_simulated(data): return data.get('simulated') == SIMULATION_KEY

def calculate_distance(point1, point2):
    lat1, lon1, lat2, lon2 = *point1, *point2
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 3959 * 2 * math.asin(math.sqrt(a))  # Earth radius in miles

def is_bid_matching(bid, robot_data):
    bid_description, robot_description = bid.get('service'), robot_data.get('service')
    if not (bid_description and robot_description): 
        return False
    if not (matched_service(bid_description and robot_description)):
        return False
    bid_location, robot_location = (bid.get('lat', 0), bid.get('lon', 0)), (robot_data.get('lat', 0), robot_data.get('lon', 0))
    if calculate_distance(bid_location, robot_location) > robot_data.get("max_distance", 1):
        return False
    return bid.get('end_time', 0) > time.time()

def grab_job(data):
    if not all(key in data for key in ['services', 'lat', 'lon', 'max_distance']):
        return {"error": "Missing required parameters"}, 400
    matched_bids = [(bid.get('price', 0), bid_id.decode(), json.loads(bid_json)) 
                    for bid_id, bid_json in redis_client.hscan_iter(REDHASH_ALL_LIVE_BIDS) 
                    if is_bid_matching(json.loads(bid_json), data)]
    if not matched_bids:
        print('no matched bids')
        return {}, 204
    _, bid_id, job = max(matched_bids, key=lambda x: x[0])
    job_id = str(uuid.uuid4())
    new_job = {
        'job_id': job_id, 'bid_id': bid_id, 'status': 'won',
        'job_request': {k: v for k, v in data.items() if isinstance(v, (str, int, float, bool, list, dict))},
        'bid_params': job,
    }
    redis_client.hset(REDHASH_ALL_WINS, bid_id, json.dumps(new_job))
    redis_client.hdel(REDHASH_ALL_LIVE_BIDS, bid_id)
    return new_job, 200

def has_sufficient_funds(username, bid_price):
    account = json.loads(redis_client.hget(REDHASH_ACCOUNTS, username) or '{}')
    balance = account.get("balance", 0)
    outstanding = sum(json.loads(b).get("price", 0) for _, b in redis_client.hscan_iter(REDHASH_ALL_LIVE_BIDS) 
                      if json.loads(b).get("username") == username)
    return balance - outstanding - bid_price >= 0

def submit_bid(data):
    bid = data.get('bid', {})
    if not all(param in bid for param in ['service', 'lat', 'lon', 'price', 'end_time']):
        return {"error": "Missing required parameters"}, 400
    if not has_sufficient_funds(data['username'], bid['price']):
        return {"error": "Insufficient funds"}, 403
    bid_id = str(uuid.uuid4())
    bid['username'] = data['username']
    bid["simulated"] = is_simulated(data)
    redis_client.hset(REDHASH_ALL_LIVE_BIDS, bid_id, json.dumps(bid))
    return {"bid_id": bid_id}, 200

def nearby_activity(data):
    if 'lat' not in data or 'lon' not in data:
        return {"error": "Missing required parameters"}, 400
    user_location = data['lat'], data['lon']
    nearby_radius = 10  # miles
    nearby_deals = {
        deal_id.decode('utf-8'): deal for deal_id, deal_json in redis_client.hgetall(REDHASH_ALL_WINS).items()
        if (deal := json.loads(deal_json)) and calculate_distance(user_location, (deal['bid_params'].get('lat', 0), deal['bid_params'].get('lon', 0))) <= nearby_radius
    }
    return nearby_deals, 200

if __name__ == "__main__":
    print("This is the main module. Run tests.py to execute the tests.")
