import uuid, redis, json, math, time, hashlib
from config import SIMULATION_KEY, REDHASH_ALL_LIVE_BIDS, REDHASH_ALL_WINS, REDHASH_ACCOUNTS, REDHASH_SIMULATED_ALL_LIVE_BIDS, REDHASH_SIMULATED_ALL_WINS
from match import matched_service

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

def is_simulated(data): return data.get('simulated') == SIMULATION_KEY

def calculate_distance(point1, point2):
    lat1, lon1, lat2, lon2 = *point1, *point2
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 3959 * 2 * math.asin(math.sqrt(a))

def is_bid_matching(bid, robot_data):
    bid_description, robot_description = bid.get('service'), robot_data.get('service')
    if not (bid_description and robot_description): 
        return False
    if not matched_service(bid_description, robot_description):
        return False
    bid_location, robot_location = (bid.get('lat', 0), bid.get('lon', 0)), (robot_data.get('lat', 0), robot_data.get('lon', 0))
    return (calculate_distance(bid_location, robot_location) <= robot_data.get("max_distance", 1) and
            bid.get('end_time', 0) > time.time())

def grab_job(data):
    if not all(key in data for key in ['service', 'lat', 'lon', 'max_distance']):
        return {"error": "Missing required fields"}, 400

    # Determine whether to query simulated bids or real bids
    bids_hash = REDHASH_SIMULATED_ALL_LIVE_BIDS if is_simulated(data) else REDHASH_ALL_LIVE_BIDS
    wins_hash = REDHASH_SIMULATED_ALL_WINS if is_simulated(data) else REDHASH_ALL_WINS
    
    matched_bids = []
    for bid_id, bid_json in redis_client.hscan_iter(bids_hash):
        try:
            bid = json.loads(bid_json)
            if is_bid_matching(bid, data):
                matched_bids.append((bid.get('price', 0), bid_id.decode(), bid))
        except json.JSONDecodeError:
            print(f"Invalid JSON for bid {bid_id}")
    
    if not matched_bids:
        return {}, 204
    
    _, bid_id, job = max(matched_bids, key=lambda x: x[0])
    job_id = str(uuid.uuid4())
    new_job = {
        'job_id': job_id,
        'bid_id': bid_id,
        'status': 'won',
        'service': job['service'],
        'lat': job['lat'],
        'lon': job['lon'],
        'price': job['price'],
        'end_time': job['end_time'],
        'buyer_username': job['username'],
        'seller_username': data['username']
    }
    
    redis_client.hset(wins_hash, job_id, json.dumps(new_job))
    redis_client.hdel(bids_hash, bid_id)
    
    return new_job, 200

def submit_bid(data):
    required_params = ['service', 'lat', 'lon', 'price', 'end_time']
    if not all(param in data for param in required_params):
        return {"error": "Missing required parameters"}, 400
    
    bid_id = str(uuid.uuid4())
    bid = {param: data[param] for param in required_params}
    bid['username'] = data['username']
    bid["simulated"] = is_simulated(data)
    
    # Store simulated bids in a separate hash
    bids_hash = REDHASH_SIMULATED_ALL_LIVE_BIDS if is_simulated(data) else REDHASH_ALL_LIVE_BIDS
    redis_client.hset(bids_hash, bid_id, json.dumps(bid))
    
    return {"bid_id": bid_id}, 200

def nearby_activity(data):
    if 'lat' not in data or 'lon' not in data:
        return {"error": "Missing required parameters"}, 400
    user_location = data['lat'], data['lon']
    nearby_radius = 10  # miles
    nearby_bids = {
        bid_id.decode('utf-8'): bid for bid_id, bid_json in redis_client.hgetall(REDHASH_ALL_LIVE_BIDS).items()
        if (bid := json.loads(bid_json)) and calculate_distance(user_location, (bid.get('lat', 0), bid.get('lon', 0))) <= nearby_radius
    }
    return nearby_bids, 200

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, provided_password):
    return stored_hash == hash_password(provided_password)

def sign_job(data):
    username = data.get('username')
    job_id = data.get('job_id')
    password = data.get('password')
    star_rating = data.get('star_rating')
    
    if not all([username, job_id, password, star_rating]):
        return {"error": "Missing required parameters"}, 400
    
    # Determine whether to query simulated wins or real wins
    wins_hash = REDHASH_SIMULATED_ALL_WINS if is_simulated(data) else REDHASH_ALL_WINS

    job = json.loads(redis_client.hget(wins_hash, job_id) or '{}')
    if not job:
        return {"error": "Job not found"}, 404
    
    user_type = 'buyer' if username == job['buyer_username'] else 'seller'
    counterparty = job['seller_username'] if user_type == 'buyer' else job['buyer_username']
    
    user_data = json.loads(redis_client.hget(REDHASH_ACCOUNTS, username) or '{}')
    if not user_data:
        return {"error": "User not found"}, 404
    
    if not verify_password(user_data['password'], password):
        return {"error": "Invalid password"}, 403
    
    if f"{user_type}_signed" in job:
        return {"error": "Job already signed by this user"}, 400
    
    job[f"{user_type}_signed"] = True
    job[f"{user_type}_rating"] = star_rating
    
    counterparty_data = json.loads(redis_client.hget(REDHASH_ACCOUNTS, counterparty) or '{}')
    counterparty_data['stars'] = counterparty_data.get('stars', 0) + star_rating
    counterparty_data['total_ratings'] = counterparty_data.get('total_ratings', 0) + 1
    
    redis_client.hset(wins_hash, job_id, json.dumps(job))
    redis_client.hset(REDHASH_ACCOUNTS, counterparty, json.dumps(counterparty_data))
    
    return {"message": "Job signed successfully"}, 200

if __name__ == "__main__":
    print("This is the main module. Run tests.py to execute the tests.")