import uuid, redis, json, math, time, config
from match import matched_service
from werkzeug.security import generate_password_hash, check_password_hash

redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)

def is_simulated(data):
    # Check if the data is marked as simulated
    return data.get('simulated') == config.SIMULATION_KEY

def calculate_distance(point1, point2):
    # Calculate the great-circle distance between two points using the Haversine formula
    lat1, lon1, lat2, lon2 = *point1, *point2
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 3959 * 2 * math.asin(math.sqrt(a))  # Radius of Earth in miles

def is_bid_matching(bid, robot_data):
    # Check if a bid matches the requirements of a robot
    bid_description = bid.get('service')
    robot_description = robot_data.get('capabilities')
    if not (bid_description and robot_description):
        return False
    if not matched_service(bid_description, robot_description):
        return False
    bid_location = (bid.get('lat', 0), bid.get('lon', 0))
    robot_location = (robot_data.get('lat', 0), robot_data.get('lon', 0))
    distance = calculate_distance(bid_location, robot_location)
    return (distance <= robot_data.get("max_distance", 1) and
            bid.get('end_time', 0) > time.time())  # Check distance and that bid has not expired

def grab_job(data):
    try:
        print(f"grab_job called with data: {json.dumps(data, indent=2)}")
        required_fields = ['capabilities', 'lat', 'lon', 'max_distance']
        if not all(key in data for key in required_fields):
            return {"error": "Missing required fields"}, 400

        # Determine whether to use simulated or real data
        bids_hash = config.REDHASH_SIMULATED_ALL_LIVE_BIDS if is_simulated(data) else config.REDHASH_ALL_LIVE_BIDS
        wins_hash = config.REDHASH_SIMULATED_ALL_WINS if is_simulated(data) else config.REDHASH_ALL_WINS

        print(f"Checking for bids in hash: {bids_hash}")
        matched_bids = []
        # Iterate over all bids to find matching ones
        for bid_id, bid_json in redis_client.hscan_iter(bids_hash):
            try:
                bid = json.loads(bid_json)
                print(f"Checking bid: {bid_id.decode()}, {json.dumps(bid, indent=2)}")
                if is_bid_matching(bid, data):
                    matched_bids.append((bid.get('price', 0), bid_id.decode(), bid))
            except json.JSONDecodeError:
                print(f"Invalid JSON for bid {bid_id.decode()}")

        if not matched_bids:
            print("No matched bids found")
            if is_simulated(data):
                # Create a fake job if no matches are found in a simulation
                fake_job_id = str(uuid.uuid4())
                fake_job = {
                    'job_id': fake_job_id,
                    'bid_id': str(uuid.uuid4()),
                    'status': 'won',
                    'service': data['service'],
                    'lat': data['lat'],
                    'lon': data['lon'],
                    'price': 50,
                    'end_time': int(time.time()) + 3600,
                    'buyer_username': 'simulated_buyer',
                    'seller_username': data['username']
                }
                print(f"Creating simulated job: {json.dumps(fake_job, indent=2)}")
                redis_client.hset(wins_hash, fake_job_id, json.dumps(fake_job))
                return fake_job, 200
            return {}, 204

        # Select the highest-priced matching bid
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

        print(f"Creating new job: {json.dumps(new_job, indent=2)}")
        # Store the new job and remove the bid
        redis_client.hset(wins_hash, job_id, json.dumps(new_job))
        redis_client.hdel(bids_hash, bid_id)

        return new_job, 200
    except Exception as e:
        print(f"Error in grab_job: {str(e)}")
        return {"error": "Internal server error"}, 500

def submit_bid(data):
    try:
        print(f"submit_bid called with data: {json.dumps(data, indent=2)}")
        required_params = ['service', 'lat', 'lon', 'price', 'end_time']
        if not all(param in data for param in required_params):
            return {"error": "Missing required parameters"}, 400

        # Create a unique bid ID
        bid_id = str(uuid.uuid4())
        bid = {param: data[param] for param in required_params}
        bid['username'] = data['username']
        bid["simulated"] = data.get('simulated', False)

        # Determine where to store the bid
        bids_hash = config.REDHASH_SIMULATED_ALL_LIVE_BIDS if is_simulated(data) else config.REDHASH_ALL_LIVE_BIDS
        print(f"Storing bid in hash: {bids_hash}")
        redis_client.hset(bids_hash, bid_id, json.dumps(bid))
        print(f"Bid stored with ID: {bid_id}")

        return {"bid_id": bid_id}, 200
    except Exception as e:
        print(f"Error in submit_bid: {str(e)}")
        return {"error": "Internal server error"}, 500

def nearby_activity(data):
    try:
        print(f"nearby_activity called with data: {json.dumps(data, indent=2)}")
        if 'lat' not in data or 'lon' not in data:
            return {"error": "Missing required parameters"}, 400
        user_location = data['lat'], data['lon']
        nearby_radius = 10  # miles
        bids_hash = config.REDHASH_SIMULATED_ALL_LIVE_BIDS if is_simulated(data) else config.REDHASH_ALL_LIVE_BIDS
        nearby_bids = {}
        # Iterate over all bids and find those within the specified radius
        for bid_id, bid_json in redis_client.hgetall(bids_hash).items():
            try:
                bid = json.loads(bid_json)
                bid_location = bid.get('lat', 0), bid.get('lon', 0)
                distance = calculate_distance(user_location, bid_location)
                if distance <= nearby_radius:
                    nearby_bids[bid_id.decode('utf-8')] = bid  # Decode bid_id from bytes to str
            except json.JSONDecodeError:
                print(f"Invalid JSON for bid {bid_id.decode()}")
        print(f"Found {len(nearby_bids)} nearby bids")
        return nearby_bids, 200
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

        # Determine where to look for the job
        wins_hash = config.REDHASH_SIMULATED_ALL_WINS if is_simulated(data) else config.REDHASH_ALL_WINS

        # Retrieve the job data
        job_json = redis_client.hget(wins_hash, job_id)
        if not job_json:
            return {"error": "Job not found"}, 404

        job = json.loads(job_json)
        print(f"Retrieved job: {json.dumps(job, indent=2)}")

        user_type = 'buyer' if username == job['buyer_username'] else 'seller'
        counterparty = job['seller_username'] if user_type == 'buyer' else job['buyer_username']

        # Retrieve user data to verify password
        user_data_json = redis_client.hget(config.REDHASH_ACCOUNTS, username)
        if not user_data_json:
            return {"error": "User not found"}, 404

        user_data = json.loads(user_data_json)
        if not check_password_hash(user_data.get('password', ''), password):
            return {"error": "Invalid password"}, 403

        # Check if the job is already signed by this user
        if f"{user_type}_signed" in job:
            return {"error": "Job already signed by this user"}, 400

        # Mark the job as signed and add the rating
        job[f"{user_type}_signed"] = True
        job[f"{user_type}_rating"] = star_rating

        # Update the counterparty's rating data
        counterparty_data_json = redis_client.hget(config.REDHASH_ACCOUNTS, counterparty)
        if counterparty_data_json:
            counterparty_data = json.loads(counterparty_data_json)
            counterparty_data['stars'] = counterparty_data.get('stars', 0) + star_rating
            counterparty_data['total_ratings'] = counterparty_data.get('total_ratings', 0) + 1
            redis_client.hset(config.REDHASH_ACCOUNTS, counterparty, json.dumps(counterparty_data))

        print(f"Updating job: {json.dumps(job, indent=2)}")
        redis_client.hset(wins_hash, job_id, json.dumps(job))

        return {"message": "Job signed successfully"}, 200
    except Exception as e:
        print(f"Error in sign_job: {str(e)}")
        return {"error": "Internal server error"}, 500

def hash_password(password):
    # Generate a hashed password
    return generate_password_hash(password)

def verify_password(stored_hash, provided_password):
    # Verify a provided password against a stored hash
    return check_password_hash(stored_hash, provided_password)

if __name__ == "__main__":
    print("This is the main module. Run tests.py to execute the tests.")
