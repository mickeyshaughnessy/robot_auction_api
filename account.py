"""
Account handler for the Robot Services Exchange API:
- /account - Get user account information and bids
"""
import json, time
from utils import redis_client
import config

def get_account(data):
    """
    Get account information for the authenticated user.
    
    Parameters:
    - username: Authenticated username (auto-injected by token_required decorator)
    - include_bids: Optional boolean to include user's bids (default: true)
    - bid_status: Optional filter for bid status (pending, matched, completed, cancelled)
    - limit: Optional maximum number of bids to retrieve (default: 20)
    
    Returns:
    - Account information including profile data and optionally bids
    """
    try:
        print(f"get_account called with data: {json.dumps(data, indent=2)}")
        
        username = data.get('username')
        if not username:
            return {"error": "Authentication required"}, 401
            
        # Get account data
        account_json = redis_client.hget(config.REDHASH_ACCOUNTS, username)
        if not account_json:
            return {"error": "Account not found"}, 404
            
        if isinstance(account_json, bytes):
            account_json = account_json.decode('utf-8')
            
        account = json.loads(account_json)
        
        # Prepare account response
        account_data = {
            "username": username,
            "created_on": account.get("created_on", 0),
            "stars": account.get("stars", 0),
            "total_ratings": account.get("total_ratings", 0),
            "account_status": account.get("status", "active")
        }
        
        # Include bids if requested (default to True)
        include_bids = data.get("include_bids", "true").lower() != "false"
        
        if include_bids:
            # Get all bids
            all_bids_json = redis_client.hgetall(config.REDHASH_ALL_LIVE_BIDS)
            
            # Filter bids by username
            user_bids = []
            for bid_id, bid_json in all_bids_json.items():
                if isinstance(bid_json, bytes):
                    bid_json = bid_json.decode('utf-8')
                
                bid = json.loads(bid_json)
                if bid.get('username') == username:
                    # Add bid_id to the bid data
                    bid['id'] = bid_id.decode() if isinstance(bid_id, bytes) else bid_id
                    user_bids.append(bid)
            
            # Filter by status if specified
            status_filter = data.get('bid_status')
            if status_filter:
                user_bids = [bid for bid in user_bids if bid.get('status') == status_filter]
            
            # Sort by creation time, newest first
            user_bids.sort(key=lambda x: x.get('created_at', 0), reverse=True)
            
            # Apply limit
            limit = int(data.get('limit', 20))
            user_bids = user_bids[:limit]
            
            # Add bids to account data
            account_data['bids'] = user_bids
        
        return account_data, 200
        
    except Exception as e:
        print(f"Error in get_account: {str(e)}")
        return {"error": "Internal server error"}, 500