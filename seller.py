"""
Seller endpoints for the Robot Services Exchange API:
- /grab_job - Accept available matching jobs
"""

import json, time, uuid, hashlib
from utils import redis_client, calculate_distance, seats
from match import matched_service
import config

def is_bid_matching(bid, robot_data):
    bid_description = bid.get('service')
    robot_description = robot_data.get('capabilities')
    
    if not (bid_description and robot_description):
        return False
        
    if not matched_service(bid_description, robot_description):
        return False
        
    bid_location = bid.get('lat', 0), bid.get('lon', 0)
    robot_location = robot_data.get('lat', 0), robot_data.get('lon', 0)
    distance = calculate_distance(bid_location, robot_location)
    
    return (distance <= robot_data.get("max_distance", 1) and
            bid.get('end_time', 0) > time.time())

def grab_job(data):
    try:
        print(f"grab_job called with data: {json.dumps(data, indent=2)}")
        
        required_fields = ['capabilities', 'lat', 'lon', 'max_distance', 'seat']
        if not all(key in data for key in required_fields):
            return {"error": "Missing required fields"}, 400

        # Verify seat credentials
        seat = data['seat']
        if seat['id'] not in seats:
            return {"error": "Invalid seat ID"}, 403
            
        stored_seat = seats[seat['id']]
        if (seat['owner'] != stored_seat['owner'] or 
            seat['secret'] != hashlib.md5(stored_seat['phrase'].encode()).hexdigest()):
            return {"error": "Invalid seat credentials"}, 403

        # Find matching bids
        matched_bids = []
        for bid_id, bid_json in redis_client.hscan_iter(config.REDHASH_ALL_LIVE_BIDS):
            try:
                if isinstance(bid_json, bytes):
                    bid_json = bid_json.decode('utf-8')
                bid = json.loads(bid_json)
                
                if is_bid_matching(bid, data):
                    matched_bids.append((bid.get('price', 0), bid_id.decode(), bid))
            except json.JSONDecodeError:
                print(f"Invalid JSON for bid {bid_id.decode()}")
                
        if not matched_bids:
            return {}, 204
            
        # Select highest-priced match
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
            'seller_username': data.get('username', 'unknown')
        }

        # Store job and remove bid
        redis_client.hset(config.REDHASH_ALL_WINS, job_id, json.dumps(new_job))
        redis_client.hdel(config.REDHASH_ALL_LIVE_BIDS, bid_id)
        
        return new_job, 200
        
    except Exception as e:
        print(f"Error in grab_job: {str(e)}")
        return {"error": "Internal server error"}, 500