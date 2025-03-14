"""
Buyer endpoints for the Robot Services Exchange API:
- /submit_bid - Submit a new service bid
- /cancel_bid - Cancel a pending bid
"""
import json, time, uuid
from utils import redis_client
import config

def submit_bid(data):
    """
    Submit a new bid for a robot service.
    
    Parameters:
    - username: Authenticated username (auto-injected by token_required decorator)
    - service: Detailed description of service requested
    - lat: Latitude of the service location
    - lon: Longitude of the service location
    - price: Bid price for the service (in USD)
    - end_time: Unix timestamp for when the bid expires
    
    Returns:
    - bid_id on success
    """
    try:
        print(f"submit_bid called with data: {json.dumps(data, indent=2)}")
        
        required_params = ['service', 'lat', 'lon', 'price', 'end_time']
        if not all(param in data for param in required_params):
            return {"error": "Missing required parameters"}, 400
            
        # Validate coordinates
        try:
            lat = float(data['lat'])
            lon = float(data['lon'])
            if lat < -90 or lat > 90 or lon < -180 or lon > 180:
                return {"error": "Invalid coordinates"}, 400
            data['lat'] = lat
            data['lon'] = lon
        except ValueError:
            return {"error": "Coordinates must be numeric"}, 400
            
        # Validate price
        try:
            price = float(data['price'])
            if price <= 0:
                return {"error": "Price must be positive"}, 400
            data['price'] = price
        except ValueError:
            return {"error": "Price must be numeric"}, 400
            
        # Create bid
        bid_id = str(uuid.uuid4())
        bid = {param: data[param] for param in required_params}
        bid['username'] = data['username']
        bid['status'] = 'pending'
        bid['created_at'] = int(time.time())
        
        # Store bid in Redis
        redis_client.hset(config.REDHASH_ALL_LIVE_BIDS, bid_id, json.dumps(bid))
        
        return {"bid_id": bid_id}, 200
        
    except Exception as e:
        print(f"Error in submit_bid: {str(e)}")
        return {"error": "Internal server error"}, 500

def cancel_bid(data):
    """
    Cancel a pending bid created by the authenticated user.
    
    Parameters:
    - username: Authenticated username (auto-injected by token_required decorator)
    - bid_id: ID of the bid to cancel
    
    Returns:
    - Success message on successful cancellation
    """
    try:
        print(f"cancel_bid called with data: {json.dumps(data, indent=2)}")
        
        # Check if bid_id is provided
        if 'bid_id' not in data:
            return {"error": "Missing bid_id parameter"}, 400
        
        bid_id = data['bid_id']
        username = data['username']
        
        # Get bid details
        bid_json = redis_client.hget(config.REDHASH_ALL_LIVE_BIDS, bid_id)
        if not bid_json:
            return {"error": "Bid not found"}, 404
            
        if isinstance(bid_json, bytes):
            bid_json = bid_json.decode('utf-8')
            
        bid = json.loads(bid_json)
        
        # Check if user owns the bid
        if bid.get('username') != username:
            return {"error": "You can only cancel your own bids"}, 403
            
        # Check if bid can be cancelled
        if bid.get('status', 'pending') != 'pending':
            return {"error": f"Cannot cancel bid with status: {bid.get('status')}"}, 400
            
        # Update bid status
        bid['status'] = 'cancelled'
        bid['cancelled_at'] = int(time.time())
        redis_client.hset(config.REDHASH_ALL_LIVE_BIDS, bid_id, json.dumps(bid))
        
        return {"message": "Bid cancelled successfully"}, 200
        
    except Exception as e:
        print(f"Error in cancel_bid: {str(e)}")
        return {"error": "Internal server error"}, 500