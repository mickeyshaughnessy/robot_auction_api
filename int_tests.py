import requests
import json
import redis
import time
import uuid

API_BASE_URL = "http://localhost:5001"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

def setup_redis():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

def cleanup_redis(r):
    for key in r.scan_iter("REDHASH_TEST*"):
        r.delete(key)

def run_test(description, test_function, *args):
    try:
        result, message = test_function(*args)
        if result:
            print(f"PASS: {description}")
        else:
            print(f"FAIL: {description} - {message}")
        return result
    except Exception as e:
        print(f"ERROR: {description} - {str(e)}")
        return False

def run_tests():
    r = setup_redis()
    cleanup_redis(r)

    try:
        # Test ping route
        def test_ping():
            response = requests.get(f"{API_BASE_URL}/ping")
            return response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        run_test("Ping route", test_ping)

        # Test buyer registration
        def test_buyer_registration():
            data = {"username": "test_buyer", "password": "password", "user_type": "buyer"}
            response = requests.post(f"{API_BASE_URL}/register", json=data)
            return response.status_code == 201, f"Expected status code 201, got {response.status_code}. Response: {response.text}"
        run_test("Buyer registration", test_buyer_registration)

        # Test seller registration
        def test_seller_registration():
            data = {"username": "test_seller", "password": "password", "user_type": "seller"}
            response = requests.post(f"{API_BASE_URL}/register", json=data)
            return response.status_code == 201, f"Expected status code 201, got {response.status_code}. Response: {response.text}"
        run_test("Seller registration", test_seller_registration)

        # Test buyer login
        def test_buyer_login():
            data = {"username": "test_buyer", "password": "password"}
            response = requests.post(f"{API_BASE_URL}/login", json=data)
            if response.status_code != 200:
                return False, f"Expected status code 200, got {response.status_code}. Response: {response.text}"
            json_data = response.json()
            return "access_token" in json_data, "Response does not contain access_token"
        run_test("Buyer login", test_buyer_login)

        # Test seller login
        def test_seller_login():
            data = {"username": "test_seller", "password": "password"}
            response = requests.post(f"{API_BASE_URL}/login", json=data)
            if response.status_code != 200:
                return False, f"Expected status code 200, got {response.status_code}. Response: {response.text}"
            json_data = response.json()
            return "access_token" in json_data, "Response does not contain access_token"
        run_test("Seller login", test_seller_login)

        # Test account balance
        def test_account_balance():
            response = requests.get(f"{API_BASE_URL}/account_balance?username=test_buyer")
            if response.status_code != 200:
                return False, f"Expected status code 200, got {response.status_code}. Response: {response.text}"
            json_data = response.json()
            return "balance" in json_data, "Response does not contain balance"
        run_test("Account balance", test_account_balance)

        # Test bid submission
        def test_bid_submission():
            bid_data = {
                "bid": {
                    "service": "cleaning",
                    "lat": 40.7128,
                    "lon": -74.0060,
                    "price": 50,
                    "end_time": int(time.time()) + 3600
                },
                "simulated": True,
                "account_id": "test_buyer",
                "bid_price": 50
            }
            response = requests.post(f"{API_BASE_URL}/make_bid", json=bid_data)
            if response.status_code != 200:
                return False, f"Expected status code 200, got {response.status_code}. Response: {response.text}"
            return response.json() is not None, "Response does not contain bid_id"
        run_test("Bid submission", test_bid_submission)

        # Test nearby activity
        def test_nearby_activity():
            data = {"lat": 40.7128, "lon": -74.0060}
            response = requests.post(f"{API_BASE_URL}/nearby", json=data)
            if response.status_code != 200:
                return False, f"Expected status code 200, got {response.status_code}. Response: {response.text}"
            nearby_bids = response.json()
            return len(nearby_bids) > 0, f"Expected at least one nearby bid, got {len(nearby_bids)}"
        run_test("Nearby activity", test_nearby_activity)

        # Test grab job
        def test_grab_job():
            robot_data = {
                "services": ["cleaning"],
                "lat": 40.7128,
                "lon": -74.0060,
                "max_distance": 1
            }
            response = requests.post(f"{API_BASE_URL}/grab_job", json=robot_data)
            if response.status_code != 200:
                return False, f"Expected status code 200, got {response.status_code}. Response: {response.text}"
            job = response.json()
            return job.get("status") == "won", f"Expected job status 'won', got {job.get('status')}"
        run_test("Grab job", test_grab_job)

    finally:
        cleanup_redis(r)

if __name__ == "__main__":
    run_tests()
