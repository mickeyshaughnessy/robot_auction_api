"""
Shared endpoints for the Robot Services Exchange API:
- /nearby - Find services and jobs near a location
- /sign_job - Complete a job with rating
"""

import json, time
from utils import redis_client, verify_password, calculate_distance
import config

def nearby_activity(data):
    try:
        print(f"nearby_activity called with data: {json.dumps(data, indent=2)}")
        if 'lat' not in data or 'lon' not in data:
            return {"error": "Missing required parameters"}, 400

        user_location = data['lat'], data['lon']
        nearby_radius = 10  # miles

        # Get nearby bids
        bids = {}
        for bid_id, bid_json in redis_client.hgetall(config.REDHASH_ALL_LIVE_BIDS).items():
            try:
                if isinstance(bid_json, bytes):
                    bid_json = bid_json.decode('utf-8')
                bid = json.loads(bid_json)
                bid_location = bid.get('lat', 0), bid.get('lon', 0)
                distance = calculate_distance(user_location, bid_location)
                if distance <= nearby_radius:
                    bids[bid_id.decode('utf-8')] = bid
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error processing bid {bid_id}: {e}")

        return {"bids": bids}, 200

    except Exception as e:
        print(f"Error in nearby_activity: {str(e)}")
        return {"error": "Internal server error"}, 500

def sign_job(data):
    try:
        print(f"sign_job called with data: {json.dumps(data, indent=2)}")
        username = data.get('username')
        job_id = data.get('job_id')
        password = data.get('password')
        star_rating = data.get('star_rating')

        if not all([username, job_id, password, star_rating]):
            return {"error": "Missing required parameters"}, 400

        # Validate star rating
        try:
            star_rating = float(star_rating)
            if not (1 <= star_rating <= 5):
                return {"error": "Star rating must be between 1 and 5"}, 400
        except (ValueError, TypeError):
            return {"error": "Invalid star rating format"}, 400

        # Get job data
        job_json = redis_client.hget(config.REDHASH_ALL_WINS, job_id)
        if not job_json:
            return {"error": "Job not found"}, 404

        if isinstance(job_json, bytes):
            job_json = job_json.decode('utf-8')
        job = json.loads(job_json)

        # Determine user role
        if username == job.get('buyer_username'):
            user_type = 'buyer'
            counterparty = job.get('seller_username')
        elif username == job.get('seller_username'):
            user_type = 'seller'
            counterparty = job.get('buyer_username')
        else:
            return {"error": "User not associated with this job"}, 403

        # Verify password
        user_data = redis_client.hget(config.REDHASH_ACCOUNTS, username)
        if not user_data:
            return {"error": "User not found"}, 404

        if isinstance(user_data, bytes):
            user_data = user_data.decode('utf-8')
        user_data = json.loads(user_data)
        
        if not verify_password(user_data.get('password', ''), password):
            return {"error": "Invalid password"}, 403

        # Check if already signed
        if f"{user_type}_signed" in job:
            return {"error": "Job already signed by this user"}, 400

        # Update job and counterparty rating
        job[f"{user_type}_signed"] = True
        job[f"{user_type}_rating"] = star_rating

        # Update counterparty rating
        if counterparty_data := redis_client.hget(config.REDHASH_ACCOUNTS, counterparty):
            if isinstance(counterparty_data, bytes):
                counterparty_data = counterparty_data.decode('utf-8')
            counterparty_data = json.loads(counterparty_data)
            counterparty_data['stars'] = counterparty_data.get('stars', 0) + star_rating
            counterparty_data['total_ratings'] = counterparty_data.get('total_ratings', 0) + 1
            redis_client.hset(config.REDHASH_ACCOUNTS, counterparty, json.dumps(counterparty_data))

        redis_client.hset(config.REDHASH_ALL_WINS, job_id, json.dumps(job))
        
        return {"message": "Job signed successfully"}, 200

    except Exception as e:
        print(f"Error in sign_job: {str(e)}")
        return {"error": "Internal server error"}, 500