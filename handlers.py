import uuid, redis, json, math

redis = redis.StrictRedis()

def distance((x1, y1), (x2, y2)):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

def matches(bid, robot_data):
    
    # Check that the robot can do the job
    res = bid.get('service') in robot_data.get('services', [])
    if res == False:
        return res
    # Check that the robot timeframe and the bid timeframe overlap  ## time in utc timestamp
    res = bid.get('end_time', 0) < robot_data.get('end_time', 1)
    if res == False:
        return res
    # Check that the travel distance is acceptable # later factor in distance
    res = distance((robot_data.get(lat,0) - bid.get(lat,0)), (robot_data.get(lon,0) - bid.get(lon,0))) < robot_data.get("max_distance") 
    if res == False:
        return res
    return True

def grab_job(data):
    # get all matching bids
    matched = []
    for bid_id, bid in redis.hscan_iter("REDHASH_ALL_LIVE_BIDS"):
        if matches(json.loads(bid)):
    matched.append(bid.get('price',0), bid_id, bid)) 
    # select the highest
    _m = sorted(matched, key = lambda x : -x[0])
    job = _m[0]
    return job 


def submit_bid(data):
    # check bid certificate
    bid = data.get('bid', {})
    # make bid_id
    bid_id = str(uuid.uuid4())
    # create bid / put bid in redis
    redis.hset("REDHASH_ALL_LIVE_BIDS", bid_id, json.dumps(bid) 
    return True 

def nearby_activity(data):
    # query transaction log with {data}
    return {}
