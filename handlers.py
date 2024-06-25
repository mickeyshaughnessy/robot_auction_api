import uuid, redis, json, math

redis = redis.StrictRedis()

def distance(x1, x2):
    return math.sqrt(sum([(x1[i]-x2[i])**2 for i in range(len(x1))])) 


def matches(bid, robot_data):

    #print(bid, robot_data)
    # Check that the robot can do the job
    res = bid.get('service') in robot_data.get('services', [])
    if res == False:
        return res
    print('here1')
    # Check that the robot timeframe and the bid timeframe overlap  ## time in utc timestamp
    #res = bid.get('end_time', 0) < robot_data.get('end_time', 1)
    #if res == False:
    #    return res
    #print('here1')
    # Check that the travel distance is acceptable # later factor in distance
    res = distance((robot_data.get('lat', 0), robot_data.get('lon', 0)), (bid.get('lat', 0), bid.get('lon', 0))) < robot_data.get("max_distance",1)
    #print(distance((robot_data.get('lat', 0), robot_data.get('lon', 0)), (bid.get('lat', 0), bid.get('lon', 0))))

    print(robot_data.get("max_distance"))
    print('here!')
    if res == False:
        return res
    return True

def grab_job(data):
    # get all matching bids
    matched = []
    for bid_id, bid in redis.hscan_iter("REDHASH_ALL_LIVE_BIDS"):
        bid = json.loads(bid)
        if matches(bid, data):
            matched.append((bid.get('price', 0), bid_id, bid))

    # select the highest
    if matched:
        _m = sorted(matched, key=lambda x: -x[0])
        job = _m[0][2]  # Access the bid data

        # Create a new job ID
        job_id = str(uuid.uuid4())

        # Create the job object
        new_job = {
            'job_id': job_id,
            'bid_id': _m[0][1],
            'status': 'won',
            'job_request': data,  # Include job request parameters
            'bid_params': job,  # Include bid parameters
        }

        # Move the bid to the wins hash
        redis.hset("REDHASH_ALL_WINS", _m[0][1], json.dumps(new_job)) 

        # Remove the bid from the live bids hash
        redis.hdel("REDHASH_ALL_LIVE_BIDS", _m[0][1])

        return new_job, 200
    else:
        return None, 204  # No matching bids

def sufficient_funds(data):
    # check that account has sufficient balance
    account_id = data.get("account_id",-1)
    bid_price = data.get("bid_price", 0)
    account = redis.hget("REDHASH_ACCOUNTS", account_id)
    if account and bid_price:
        account = json.loads(account)
        all_outstanding = []
        for bid_id, b in redis.hscan_iter("REDHASH_ALL_LIVE_BIDS"):
            b = json.loads(b)
            if b.get("bidder_account_id") == account_id:
                all_outstanding.append(b)
        if account.get("balance",0) - sum([b.get("bid_price",0) for b in all_outstanding]) + data.get("bid_price",0) > 0:
            response, status = {"message" : "sufficient funds"}, 200
    response, status = {"message" : "insufficient funds or malformed request"}, 400
    return True 

def certify(data):
    # check that the request is certified 
    return True

def submit_bid(data):
    # check bid certificate
    certificate = certify(data)
    if sufficient_funds(data) and certificate:
       # make bid_id
        bid = data.get('bid', {})
        bid_id = str(uuid.uuid4())
        redis.hset("REDHASH_ALL_LIVE_BIDS", bid_id, json.dumps(bid)) 
        return bid_id, 200 
    return bid_id, 403


def nearby_activity(data):
    all_live_bids = redis.hgetall("REDHASH_ALL_LIVE_BIDS")

    return json.dumps(all_live_bids), 200 



if __name__ == "__main__":
    # Test 1: Submit a bid and grab the job
    print("Test 1: Submit Bid and Grab Job")

    # Setup: Define bid and robot data
    bid_data = {
        'service': 'delivery',
        'lat': 40.7128,
        'lon': -74.0060,
        'price': 100,
        'end_time': 1680000000,  # Timestamp for future date
    }
    robot_data = {
        'services': ['delivery'],
        'lat': 40.7128,
        'lon': -74.0060,
        'max_distance': 10,
        'end_time': 1680000000,
    }

    # Submit the bid
    submit_bid({'bid': bid_data})

    # Grab the job
    job = grab_job(robot_data)

    # Check for successful job creation
    assert job is not None
    assert job['job_id'] is not None
    assert job['bid_id'] is not None
    assert job['status'] == 'won'

    # Cleanup: Remove the bid from wins hash
    redis.hdel("REDHASH_ALL_WINS", job['bid_id'])

    # Test 2: Submit a bid that doesn't match
    print("Test 2: Submit Bid that Doesn't Match")

    # Setup: Define bid data that doesn't match the robot
    bid_data = {
        'service': 'cleaning',
        'lat': 40.7128,
        'lon': -74.0060,
        'price': 100,
        'end_time': 2680000000,
    }

    # Submit the bid
    submit_bid({'bid': bid_data})

    # Grab the job
    job = grab_job(robot_data)

    # Check that no job was created
    assert job is None

    # Cleanup: Remove the bid from live bids hash (since it didn't match)
    redis.hdel("REDHASH_ALL_LIVE_BIDS", job['bid_id'])
