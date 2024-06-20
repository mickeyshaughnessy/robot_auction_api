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

        return new_job
    else:
        return None  # No matching bids

def submit_bid(data):
    # check bid certificate
    bid = data.get('bid', {})
    # make bid_id
    bid_id = str(uuid.uuid4())
    # create bid / put bid in redis
    redis.hset("REDHASH_ALL_LIVE_BIDS", bid_id, json.dumps(bid)) 
    return True 

def nearby_activity(data):
    # query transaction log with {data}
    return {}

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
