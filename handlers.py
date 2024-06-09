import redis, json

redis = redis.StrictRedis()

def hold_auction(data):
    # get all matching bids
    # select the highest
    # dispatch robot
    # pay job
    pass 

def grab_job(data):
    job = hold_auction(data)
    return job

def submit_bid(data):
    # check bid certificate
    # 
    # create bid / put bid in redis
    return bid

def nearby_services(data):
    # query transaction log with {data}
    return {}
