import requests
import json
import redis
import time
import uuid
from llm import generate_completion

API__URL = "http://localhost:5001"
REDIS_HOST, REDIS_PORT, REDIS_DB = "localhost", 6379, 0

def setup_redis():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

def cleanup_redis(r):
    for key in r.scan_iter("REDHASH_TEST*"):
        r.delete(key)

def run_test(description, test_function, *args):
    print(f"Testing: {description}")
    try:
        result, message = test_function(*args)
        print(f"{'PASS' if result else 'FAIL'}: {message}")
        return result
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def run_tests():
    r, buyer_token, seller_token = setup_redis(), None, None
    cleanup_redis(r)

    try:
        def test_ping():
            response = requests.get(f"{API__URL}/ping")
            return response.status_code == 200, f"Ping: status {response.status_code}"

        def test_buyer_registration():
            response = requests.post(f"{API__URL}/register", json={"username": "test_buyer", "password": "password", "user_type": "buyer"})
            return response.status_code == 201, f"Buyer registration: status {response.status_code}"

        def test_seller_registration():
            response = requests.post(f"{API__URL}/register", json={"username": "test_seller", "password": "password", "user_type": "seller"})
            return response.status_code == 201, f"Seller registration: status {response.status_code}"

        def test_buyer_login():
            nonlocal buyer_token
            response = requests.post(f"{API__URL}/login", json={"username": "test_buyer", "password": "password"})
            if response.status_code == 200:
                buyer_token = response.json().get("access_token")
            return response.status_code == 200, f"Buyer login: status {response.status_code}"

        def test_seller_login():
            nonlocal seller_token
            response = requests.post(f"{API__URL}/login", json={"username": "test_seller", "password": "password"})
            if response.status_code == 200:
                seller_token = response.json().get("access_token")
            return response.status_code == 200, f"Seller login: status {response.status_code}"

        def test_account_balance():
            response = requests.get(f"{API__URL}/account_balance", headers={"Authorization": buyer_token})
            return response.status_code == 200 and "balance" in response.json(), f"Account balance: status {response.status_code}"

        def test_bid_submission():
            bid_data = {
                "bid": {"service": "cleaning", "lat": 40.7128, "lon": -74.0060, "price": 50, "end_time": int(time.time()) + 3600},
                "simulated": True,
                "bid_price": 50
            }
            response = requests.post(f"{API__URL}/make_bid", json=bid_data, headers={"Authorization": buyer_token})
            return response.status_code == 200, f"Bid submission: status {response.status_code}"

        def test_nearby_activity():
            response = requests.post(f"{API__URL}/nearby", json={"lat": 40.7128, "lon": -74.0060}, headers={"Authorization": buyer_token})
            return response.status_code == 200, f"Nearby activity: status {response.status_code}, bids: {len(response.json())}"

        def test_grab_job():
            robot_data = {"service": "cleaning, gardening", "lat": 40.7128, "lon": -74.0060, "max_distance": 10}
            response = requests.post(f"{API__URL}/grab_job", json=robot_data, headers={"Authorization": seller_token})
            print(f"Grab job response status: {response.status_code}")
            print(f"Grab job response content: {response.text}")
            try:
                json_response = response.json()
                return response.status_code in [200, 204], f"Grab job: status {response.status_code}, job status: {json_response.get('status') if response.status_code == 200 else 'No job available'}"
            except json.JSONDecodeError:
                return False, f"Grab job: Invalid JSON response. Status: {response.status_code}, Content: {response.text[:100]}"

        tests = [test_ping, test_buyer_registration, test_seller_registration, test_buyer_login, test_seller_login,
                 test_account_balance, test_bid_submission, test_nearby_activity, test_grab_job]
        
        for test in tests:
            run_test(test.__name__.replace('test_', '').replace('_', ' ').capitalize(), test)

    finally:
        cleanup_redis(r)

if __name__ == "__main__":
    run_tests()
