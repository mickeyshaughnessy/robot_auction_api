import redis
import hashlib

def setup_redis(host, port, db):
    return redis.Redis(host=host, port=port, db=db)

def cleanup_redis(r):
    for key in r.scan_iter("*SIMULATED*"):
        r.delete(key)

def generate_signature(password, job_id):
    return hashlib.sha256(f"{password}{job_id}".encode()).hexdigest()
