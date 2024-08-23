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
        def test_nearby_activity():
            response = requests.post(f"{API_URL}/nearby", json={"lat": 40.7128, "lon": -74.0060}, headers={"Authorization": f"Bearer {buyer_token}"}, verify=False)
            print(f"Nearby activity response: {response.text}")
            
            all_bids = r.hgetall(config.REDHASH_ALL_LIVE_BIDS)
            print(f"All bids in Redis: {all_bids}")
            
            return response.status_code == 200, f"Nearby activity: status {response.status_code}, bids: {len(response.json())}"

        def test_sign_job():
            bid_data = {
                "service": "cleaning", "lat": 40.7128, "lon": -74.0060, "price": 50, "end_time": int(time.time()) + 3600,
                "simulated": config.SIMULATION_KEY 
            }
            bid_response = requests.post(f"{API_URL}/make_bid", json=bid_data, headers={"Authorization": f"Bearer {buyer_token}"}, verify=False)
            print(f"Bid submission response: {bid_response.text}")
            if bid_response.status_code != 200:
                return False, f"Failed to create bid for sign_job test: {bid_response.status_code}"
            
            robot_data = {"service": "cleaning", "lat": 40.7128, "lon": -74.0060, "max_distance": 10}
            grab_response = requests.post(f"{API_URL}/grab_job", json=robot_data, headers={"Authorization": f"Bearer {seller_token}"}, verify=False)
            print(f"Grab job response: {grab_response.text}")
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
            print(f"Buyer sign job response: {buyer_sign_response.text}")
            
            seller_sign_data = {
                "username": "test_seller",
                "job_id": job_id,
                "password": "password",
                "star_rating": 4
            }
            seller_sign_response = requests.post(f"{API_URL}/sign_job", json=seller_sign_data, headers={"Authorization": f"Bearer {seller_token}"}, verify=False)
            print(f"Seller sign job response: {seller_sign_response.text}")
            
            return (buyer_sign_response.status_code == 200 and seller_sign_response.status_code == 200, 
                f"Sign job: Buyer status {buyer_sign_response.status_code}, Seller status {seller_sign_response.status_code}")

        tests = [test_nearby_activity, test_sign_job]
        
        for test in tests:
            run_test(test.__name__.replace('test_', '').replace('_', ' ').capitalize(), test)

    finally:
        cleanup_redis(r)

if __name__ == "__main__":
    run_tests()