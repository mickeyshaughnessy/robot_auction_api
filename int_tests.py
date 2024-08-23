import requests, json, time, hashlib, urllib3
from utils import setup_redis, cleanup_redis
import config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = config.API_URL

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
            response = requests.get(f"{API_URL}/ping", verify=False)
            return response.status_code == 200, f"Ping: status {response.status_code}"

        def test_buyer_registration():
            response = requests.post(f"{API_URL}/register", json={"username": "test_buyer", "password": "password", "user_type": "buyer"}, verify=False)
            return response.status_code == 201, f"Buyer registration: status {response.status_code}"

        def test_seller_registration():
            response = requests.post(f"{API_URL}/register", json={"username": "test_seller", "password": "password", "user_type": "seller"}, verify=False)
            return response.status_code == 201, f"Seller registration: status {response.status_code}"

        def test_buyer_login():
            nonlocal buyer_token
            response = requests.post(f"{API_URL}/login", json={"username": "test_buyer", "password": "password"}, verify=False)
            if response.status_code == 200:
                buyer_token = response.json().get("access_token")
            return response.status_code == 200, f"Buyer login: status {response.status_code}"

        def test_seller_login():
            nonlocal seller_token
            response = requests.post(f"{API_URL}/login", json={"username": "test_seller", "password": "password"}, verify=False)
            if response.status_code == 200:
                seller_token = response.json().get("access_token")
            return response.status_code == 200, f"Seller login: status {response.status_code}"

        def test_multiple_bid_submissions():
            services = ["cleaning", "gardening", "pet_sitting"]
            bid_ids = []
            for service in services:
                bid_data = {
                    "service": service,
                    "lat": 40.7128,
                    "lon": -74.0060,
                    "price": 50,
                    "end_time": int(time.time()) + 3600,
                    "simulated": config.SIMULATION_KEY 
                }
                response = requests.post(f"{API_URL}/make_bid", json=bid_data, headers={"Authorization": f"Bearer {buyer_token}"}, verify=False)
                if response.status_code != 200:
                    return False, f"Multiple bid submission failed for {service}: status {response.status_code}"
                bid_ids.append(response.json().get('bid_id'))
            
            print(f"Submitted bid IDs: {bid_ids}")
            return True, f"Multiple bid submission: status 200 for all bids"

        def test_nearby_activity():
            response = requests.post(f"{API_URL}/nearby", json={"lat": 40.7128, "lon": -74.0060}, headers={"Authorization": f"Bearer {buyer_token}"}, verify=False)
            print(f"Nearby activity response: {response.text}")
            
            # Check Redis directly
            all_bids = r.hgetall(config.REDHASH_ALL_LIVE_BIDS)
            print(f"All bids in Redis: {all_bids}")
            
            return response.status_code == 200, f"Nearby activity: status {response.status_code}, bids: {len(response.json())}"

        def test_grab_job():
            robot_data = {"service": "cleaning, gardening", "lat": 40.7128, "lon": -74.0060, "max_distance": 10}
            response = requests.post(f"{API_URL}/grab_job", json=robot_data, headers={"Authorization": f"Bearer {seller_token}"}, verify=False)
            print(f"Grab job response: {response.text}")
            try:
                json_response = response.json()
                return response.status_code in [200, 204], f"Grab job: status {response.status_code}, job status: {json_response.get('status') if response.status_code == 200 else 'No job available'}"
            except json.JSONDecodeError:
                return False, f"Grab job: Invalid JSON response. Status: {response.status_code}, Content: {response.text[:100]}"

        def test_sign_job():
            bid_data = {
                "service": "cleaning", "lat": 40.7128, "lon": -74.0060, "price": 50, "end_time": int(time.time()) + 3600,
                "simulated": config.SIMULATION_KEY 
            }
            bid_response = requests.post(f"{API_URL}/make_bid", json=bid_data, headers={"Authorization": f"Bearer {buyer_token}"}, verify=False)
            if bid_response.status_code != 200:
                return False, f"Failed to create bid for sign_job test: {bid_response.status_code}"
            
            robot_data = {"service": "cleaning", "lat": 40.7128, "lon": -74.0060, "max_distance": 10}
            grab_response = requests.post(f"{API_URL}/grab_job", json=robot_data, headers={"Authorization": f"Bearer {seller_token}"}, verify=False)
            if grab_response.status_code != 200:
                return False, f"Failed to grab job for sign_job test: {grab_response.status_code}"
            
            job_id = grab_response.json().get('job_id')
            
            buyer_sign_data = {
                "username": "test_buyer",
                "job_id": job_id,
                "password": "password",
                "star_rating": 5
            }
            buyer_sign_response = requests.post(f"{API_URL}/sign_job", json=buyer_sign_data, headers={"Authorization": f"Bearer {buyer_token}"}, verify=False)
            
            seller_sign_data = {
                "username": "test_seller",
                "job_id": job_id,
                "password": "password",
                "star_rating": 4
            }
            seller_sign_response = requests.post(f"{API_URL}/sign_job", json=seller_sign_data, headers={"Authorization": f"Bearer {seller_token}"}, verify=False)
            
            return (buyer_sign_response.status_code == 200 and seller_sign_response.status_code == 200, 
                f"Sign job: Buyer status {buyer_sign_response.status_code}, Seller status {seller_sign_response.status_code}")

        tests = [test_ping, test_buyer_registration, test_seller_registration, test_buyer_login, test_seller_login,
                 test_multiple_bid_submissions, test_nearby_activity, test_grab_job, test_sign_job]
        
        for test in tests:
            run_test(test.__name__.replace('test_', '').replace('_', ' ').capitalize(), test)

    finally:
        cleanup_redis(r)

if __name__ == "__main__":
    run_tests()