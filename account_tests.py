import redis, os, json

# API Configuration
API_URL = "http://100.26.236.1:5001"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
SIMULATION_KEY = "sim_12345"  # For simulated testing

# Redis Hash Keys
REDHASH_ACCOUNTS = "accounts"
REDHASH_ALL_LIVE_BIDS = "live_bids"
REDHASH_SIMULATED_ALL_LIVE_BIDS = "sim_live_bids"
REDHASH_ALL_ACTIVE_JOBS = "active_jobs"
REDHASH_SIMULATED_ACTIVE_JOBS = "sim_active_jobs"

def setup_redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB):
    r = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)
    try:
        r.ping()
        return r
    except redis.ConnectionError:
        print(f"❌ Failed to connect to Redis at {host}:{port}")
        raise

def cleanup_redis(r):
    test_keys = [
        REDHASH_SIMULATED_ALL_LIVE_BIDS,
        REDHASH_SIMULATED_ACTIVE_JOBS
    ]
    
    for key in test_keys:
        r.delete(key)
    
    # Clean up test user accounts
    accounts = r.hgetall(REDHASH_ACCOUNTS)
    for username, data in accounts.items():
        if username.startswith("test_"):
            r.hdel(REDHASH_ACCOUNTS, username)
    
    # Clean up test auth tokens
    token_pattern = "auth_token:*"
    tokens = r.keys(token_pattern)
    for token in tokens:
        username = r.get(token)
        if username and username.startswith("test_"):
            r.delete(token)

def run_test(description, test_function, *args):
    print(f"\n{'='*40}")
    print(f"Testing: {description}")
    print(f"{'='*40}")
    
    try:
        result, message = test_function(*args)
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {message}")
        return result
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def get_auth_token(username="test_user", password="password123"):
    """Helper to get auth token for tests requiring authentication"""
    response = requests.post(f"{API_URL}/login", json={
        "username": username,
        "password": password
    })
    if response.status_code != 200:
        raise Exception(f"Failed to get auth token: {response.status_code}")
    return response.json()["access_token"]

def create_test_user(username="test_user", password="password123"):
    """Helper to create test user and return auth token"""
    # Register user
    response = requests.post(f"{API_URL}/register", json={
        "username": username,
        "password": password
    })
    if response.status_code != 201:
        raise Exception(f"Failed to create test user: {response.status_code}")
    
    # Get auth token
    return get_auth_token(username, password)

def random_location():
    """Generate random test coordinates centered around NYC"""
    import random
    return (
        40.7128 + (random.random() - 0.5),  # lat
        -74.0060 + (random.random() - 0.5)   # lon
    )

def assert_valid_response(response, expected_status=200):
    """Helper to validate API responses"""
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}: {response.text}"
    
    if response.status_code != 204:  # No content
        try:
            return response.json()
        except json.JSONDecodeError:
            raise AssertionError(f"Invalid JSON response: {response.text}")

class TestConfig:
    """Shared test configuration"""
    SERVICES = [
        "cleaning", "delivery", "security", "maintenance",
        "lawn_care", "pet_sitting", "home_repair", "painting"
    ]
    
    PRICES = [25, 50, 75, 100, 150, 200]
    
    @staticmethod
    def random_service():
        import random
        return random.choice(TestConfig.SERVICES)
    
    @staticmethod
    def random_price():
        import random
        return random.choice(TestConfig.PRICES)