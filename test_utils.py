import redis, os, json, requests, random

API_URL = os.getenv('API_URL', 'http://localhost:5001')
REDIS_HOST, REDIS_PORT, REDIS_DB = os.getenv('REDIS_HOST', 'localhost'), int(os.getenv('REDIS_PORT', 6379)), int(os.getenv('REDIS_DB', 0))
SIMULATION_KEY = "sim_12345"

REDHASH_ACCOUNTS = "accounts"
REDHASH_LIVE_BIDS = "live_bids" 
REDHASH_SIM_BIDS = "sim_live_bids"
REDHASH_ACTIVE_JOBS = "active_jobs"
REDHASH_SIM_JOBS = "sim_active_jobs"

def setup_redis():
    r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    try:
        r.ping()
        return r
    except redis.ConnectionError as e:
        print(f"❌ Redis connection failed: {e}")
        raise

def cleanup_redis(r):
    # Clean simulation data
    r.delete(REDHASH_SIM_BIDS, REDHASH_SIM_JOBS)
    
    # Clean test accounts
    for username in r.hkeys(REDHASH_ACCOUNTS):
        if username.startswith("test_"):
            r.hdel(REDHASH_ACCOUNTS, username)
    
    # Clean test tokens
    for token in r.keys("auth_token:*"):
        if r.get(token).startswith("test_"):
            r.delete(token)

def run_test(desc, test_fn, *args):
    print(f"\nTest: {desc}")
    try:
        result, msg = test_fn(*args)
        print("✅ PASS" if result else "❌ FAIL", msg)
        return result
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def get_auth_token(username="test_user", password="test123"):
    resp = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
    if resp.status_code != 200:
        raise Exception(f"Auth failed: {resp.status_code}")
    return resp.json()["access_token"]

def create_test_user(username="test_user", password="test123"):
    resp = requests.post(f"{API_URL}/register", json={"username": username, "password": password})
    if resp.status_code != 201:
        raise Exception(f"User creation failed: {resp.status_code}")
    return get_auth_token(username, password)

def random_location():
    return (
        40.7128 + (random.random() - 0.5),  # NYC ± 0.5°
        -74.0060 + (random.random() - 0.5)
    )

def assert_valid_response(resp, expected_status=200):
    assert resp.status_code == expected_status, f"Expected {expected_status}, got {resp.status_code}: {resp.text}"
    return resp.json() if resp.status_code != 204 else None

class TestConfig:
    SERVICES = ["cleaning", "delivery", "security", "maintenance", "lawn_care", "pet_sitting", "home_repair", "painting"]
    PRICES = [25, 50, 75, 100, 150, 200]
    
    @staticmethod
    def random_service(): return random.choice(TestConfig.SERVICES)
    
    @staticmethod 
    def random_price(): return random.choice(TestConfig.PRICES)
