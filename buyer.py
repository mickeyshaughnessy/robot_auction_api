"""
Buyer endpoints for the Robot Services Exchange API:
- /make_bid - Submit a new service bid
"""

import json, time, uuid
from utils import redis_client
import config

def submit_bid(data):
    try:
        print(f"submit_bid called with data: {json.dumps(data, indent=2)}")
        required_params = ['service', 'lat', 'lon', 'price', 'end_time']
        if not all(param in data for param in required_params):
            return {"error": "Missing required parameters"}, 400

        bid_id = str(uuid.uuid4())
        bid = {param: data[param] for param in required_params}
        bid['username'] = data['username']

        redis_client.hset(config.REDHASH_ALL_LIVE_BIDS, bid_id, json.dumps(bid))
        
        return {"bid_id": bid_id}, 200
        
    except Exception as e:
        print(f"Error in submit_bid: {str(e)}")
        return {"error": "Internal server error"}, 500