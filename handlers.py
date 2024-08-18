import uuid
import redis
import json
import math
from config import SIMULATION_KEY, REDHASH_ALL_LIVE_BIDS, REDHASH_ALL_WINS, REDHASH_ACCOUNTS
from llm import matched_service

redis_client = redis.StrictRedis()

def is_simulated(data):
    return data.get('simulated') == SIMULATION_KEY

def calculate_distance(point1, point2):
    # Haversine formula to calculate distance between two points on Earth
    lat1, lon1 = point1
    lat2, lon2 = point2
    
    R = 3959  # Radius of the Earth in miles
    
    # Convert latitude and longitude to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = R * c
    
    return distance

def is_service_match(bid_service, robot_services):
    # Use the matched_service function from llm.py
    buyer_description = f"I need a robot to perform this service: {bid_service}"
    seller_description = f"Our robot can perform these services: {', '.join(robot_services)}"
    return matched_service(buyer_description, seller_description)

def is_bid_matching(bid, robot_data):
    if not is_service_match(bid.get('service'), robot_data.get('services', [])):
        return False
    bid_location = (bid.get('lat', 0), bid.get('lon', 0))
    robot_location = (robot_data.get('lat', 0), robot_data.get('lon', 0))
    return calculate_distance(bid_location, robot_location) <= robot_data.get("max_distance", 1)

def grab_job(data):
    robot_data = data
    if not all(key in robot_data for key in ['services', 'lat', 'lon', 'max_distance']):
        return {"error": "Missing required parameters"}, 400

    matched_bids = []
    for bid_id, bid_json in redis_client.hscan_iter(REDHASH_ALL_LIVE_BIDS):
        bid = json.loads(bid_json)
        if is_bid_matching(bid, robot_data):
            matched_bids.append((bid.get('price', 0), bid_id.decode(), bid))
    
    if not matched_bids:
        return None, 204  # No Content - No matching bids found
    
    best_match = max(matched_bids, key=lambda x: x[0])
    _, bid_id, job = best_match
    job_id = str(uuid.uuid4())
    new_job = {
        'job_id': job_id,
        'bid_id': bid_id,
        'status': 'won',
        'job_request': {k: v for k, v in robot_data.items() if isinstance(v, (str, int, float, bool, list, dict))},
        'bid_params': job,
    }
    redis_client.hset(REDHASH_ALL_WINS, bid_id, json.dumps(new_job))
    redis_client.hdel(REDHASH_ALL_LIVE_BIDS, bid_id)
    return new_job, 200

def has_sufficient_funds(username, bid_price):
    account_json = redis_client.hget(REDHASH_ACCOUNTS, username)
    
    if not account_json:
        return False  # Return False if account not found
    
    try:
        account = json.loads(account_json)
    except json.JSONDecodeError:
        return False  # Return False if account data is invalid
    
    balance = account.get("balance", 0)
    all_outstanding = []
    for _, b in redis_client.hscan_iter(REDHASH_ALL_LIVE_BIDS):
        b = json.loads(b)
        if b.get("username") == username:
            all_outstanding.append(b)
    total_outstanding = sum(b.get("price", 0) for b in all_outstanding)
    
    return balance - total_outstanding - bid_price >= 0

def submit_bid(data):
    required_params = ['service', 'lat', 'lon', 'price', 'end_time']
    bid = data.get('bid', {})
    
    if not all(param in bid for param in required_params):
        return {"error": "Missing required parameters"}, 400

    if not has_sufficient_funds(data['username'], bid['price']):
        return {"error": "Insufficient funds"}, 403

    bid_id = str(uuid.uuid4())
    bid['username'] = data['username']
    
    # Mark the bid as simulated if the flag is set
    if is_simulated(data):
        bid["simulated"] = True
    
    redis_client.hset(REDHASH_ALL_LIVE_BIDS, bid_id, json.dumps(bid))
    return {"bid_id": bid_id}, 200

def nearby_activity(data):
    if 'lat' not in data or 'lon' not in data:
        return {"error": "Missing required parameters"}, 400

    user_location = (data['lat'], data['lon'])
    nearby_radius = 10  # miles

    all_completed_deals = redis_client.hgetall(REDHASH_ALL_WINS)
    nearby_deals = {}

    for deal_id, deal_json in all_completed_deals.items():
        deal = json.loads(deal_json)
        deal_location = (deal['bid_params'].get('lat', 0), deal['bid_params'].get('lon', 0))
        
        if calculate_distance(user_location, deal_location) <= nearby_radius:
            nearby_deals[deal_id.decode('utf-8')] = deal

    return nearby_deals, 200

if __name__ == "__main__":
    print("This is the main module. Run tests.py to execute the tests.")
