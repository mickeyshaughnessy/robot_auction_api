import requests, json, time, hashlib
from utils import setup_redis, cleanup_redis, generate_signature
import config

API__URL = config.API_URL
# REDIS_HOST, REDIS_PORT, REDIS_DB = "localhost", 6379, 0

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
    r, buyer_token, seller_token = setup_redis(config.REDIS_HOST, config.REDIS_PORT, config.REDIS_DB), None, None
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

        def test_bid_submission():
            bid_data = {
                "service": "cleaning", "lat": 40.7128, "lon": -74.0060, "price": 50, "end_time": int(time.time()) + 3600,
                "simulated": config.SIMULATION_KEY 
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
            try:
                json_response = response.json()
                return response.status_code in [200, 204], f"Grab job: status {response.status_code}, job status: {json_response.get('status') if response.status_code == 200 else 'No job available'}"
            except json.JSONDecodeError:
                return False, f"Grab job: Invalid JSON response. Status: {response.status_code}, Content: {response.text[:100]}"

        def test_sign_job():
            # First, create a job
            bid_data = {
                "service": "cleaning",
                "lat": 40.7128,
                "lon": -74.0060,
                "price": 50,
                "end_time": int(time.time()) + 3600,
                "simulated": config.SIMULATION_KEY 
            }
            bid_response = requests.post(f"{API__URL}/make_bid", json=bid_data, headers={"Authorization": buyer_token})
            if bid_response.status_code != 200:
                return False, f"Failed to create bid for sign_job test: {bid_response.status_code}"
            
            # Grab the job
            robot_data = {"service": "cleaning", "lat": 40.7128, "lon": -74.0060, "max_distance": 10}
            grab_response = requests.post(f"{API__URL}/grab_job", json=robot_data, headers={"Authorization": seller_token})
            if grab_response.status_code != 200:
                return False, f"Failed to grab job for sign_job test: {grab_response.status_code}"
            
            job_id = grab_response.json().get('job_id')
            
            # Sign the job as buyer
            buyer_signature = generate_signature("password", job_id)
            buyer_sign_data = {
                "username": "test_buyer",
                "job_id": job_id,
                "signature": buyer_signature,
                "star_rating": 5
            }
            buyer_sign_response = requests.post(f"{API__URL}/sign_job", json=buyer_sign_data, headers={"Authorization": buyer_token})
            
            # Sign the job as seller
            seller_signature = generate_signature("password", job_id)
            seller_sign_data = {
                "username": "test_seller",
                "job_id": job_id,
                "signature": seller_signature,
                "star_rating": 4
            }
            seller_sign_response = requests.post(f"{API__URL}/sign_job", json=seller_sign_data, headers={"Authorization": seller_token})
            
            return (buyer_sign_response.status_code == 200 and seller_sign_response.status_code == 200, 
                f"Sign job: Buyer status {buyer_sign_response.status_code}, Seller status {seller_sign_response.status_code}")

        tests = [test_ping, test_buyer_registration, test_seller_registration, test_buyer_login, test_seller_login,
                 test_bid_submission, test_nearby_activity, test_grab_job, test_sign_job]
        
        for test in tests:
            run_test(test.__name__.replace('test_', '').replace('_', ' ').capitalize(), test)

    finally:
        cleanup_redis(r)

if __name__ == "__main__":
    run_tests()