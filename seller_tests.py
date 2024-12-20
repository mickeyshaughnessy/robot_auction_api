import requests, json, time, uuid, threading
from test_utils import (run_test, API_URL, setup_redis, cleanup_redis, 
                       create_test_user, TestConfig, random_location,
                       assert_valid_response)

def run_seller_tests():
    r = setup_redis()
    print("\n=== 🤖 Seller Endpoint Tests ===")
    
    # Create test users
    test_seller = f"test_seller_{uuid.uuid4().hex[:8]}"
    test_buyer = f"test_buyer_{uuid.uuid4().hex[:8]}"
    seller_token = create_test_user(test_seller, "password123")
    buyer_token = create_test_user(test_buyer, "password123")
    seller_headers = {"Authorization": f"Bearer {seller_token}"}
    buyer_headers = {"Authorization": f"Bearer {buyer_token}"}

    def create_test_bid():
        lat, lon = random_location()
        bid_data = {
            "service": TestConfig.random_service(),
            "lat": lat,
            "lon": lon,
            "price": TestConfig.random_price(),
            "end_time": int(time.time()) + 3600
        }
        res = requests.post(f"{API_URL}/make_bid", 
                          json=bid_data, 
                          headers=buyer_headers)
        return assert_valid_response(res)

    def test_grab_job():
        # Create a bid first
        create_test_bid()
        
        # Try to grab it
        lat, lon = random_location()
        robot_data = {
            "services": ",".join(TestConfig.SERVICES),
            "lat": lat,
            "lon": lon,
            "max_distance": 50
        }
        res = requests.post(f"{API_URL}/grab_job", 
                          json=robot_data, 
                          headers=seller_headers)
        data = assert_valid_response(res)
        return "job_id" in data, f"Job grabbed with ID: {data.get('job_id')}"

    def test_grab_job_no_matching_service():
        create_test_bid()
        robot_data = {
            "services": "nonexistent_service",
            "lat": 40.7128,
            "lon": -74.0060,
            "max_distance": 10
        }
        res = requests.post(f"{API_URL}/grab_job", 
                          json=robot_data, 
                          headers=seller_headers)
        return res.status_code == 204, f"No match found: {res.status_code}"

    def test_grab_job_too_far():
        bid = create_test_bid()
        robot_data = {
            "services": ",".join(TestConfig.SERVICES),
            "lat": bid["lat"] + 100,  # Way too far
            "lon": bid["lon"] + 100,
            "max_distance": 1
        }
        res = requests.post(f"{API_URL}/grab_job", 
                          json=robot_data, 
                          headers=seller_headers)
        return res.status_code == 204, f"Distance check: {res.status_code}"

    def test_concurrent_job_grab():
        bid = create_test_bid()
        
        # Track which seller got the job
        job_owner = None
        job_lock = threading.Lock()
        
        def try_grab_job(seller_num):
            nonlocal job_owner
            seller = f"test_seller_{seller_num}"
            token = create_test_user(seller, "password123")
            headers = {"Authorization": f"Bearer {token}"}
            
            robot_data = {
                "services": ",".join(TestConfig.SERVICES),
                "lat": bid["lat"],
                "lon": bid["lon"],
                "max_distance": 50
            }
            res = requests.post(f"{API_URL}/grab_job", 
                              json=robot_data, 
                              headers=headers)
            
            if res.status_code == 200:
                with job_lock:
                    job_owner = seller_num
        
        # Launch 3 concurrent attempts
        threads = []
        for i in range(3):
            t = threading.Thread(target=try_grab_job, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        job_assigned = job_owner is not None
        return job_assigned, f"Job assigned to seller: {job_owner}"

    def test_complete_job_flow():
        # Create bid
        bid = create_test_bid()
        
        # Grab job
        robot_data = {
            "services": ",".join(TestConfig.SERVICES),
            "lat": bid["lat"],
            "lon": bid["lon"],
            "max_distance": 50
        }
        grab_res = requests.post(f"{API_URL}/grab_job", 
                               json=robot_data, 
                               headers=seller_headers)
        job = assert_valid_response(grab_res)
        
        # Sign job completion
        sign_data = {
            "job_id": job["job_id"],
            "password": "password123",
            "star_rating": 5
        }
        sign_res = requests.post(f"{API_URL}/sign_job", 
                               json=sign_data, 
                               headers=seller_headers)
        completion_success = sign_res.status_code == 200
        
        # Verify job is no longer available
        regrab_res = requests.post(f"{API_URL}/grab_job", 
                                 json=robot_data, 
                                 headers=seller_headers)
        no_longer_available = regrab_res.status_code == 204
        
        success = completion_success and no_longer_available
        return success, f"Job flow complete: {completion_success}, {no_longer_available}"

    tests = [
        ("Grab Job", test_grab_job),
        ("No Matching Service", test_grab_job_no_matching_service),
        ("Distance Check", test_grab_job_too_far),
        ("Concurrent Grab", test_concurrent_job_grab),
        ("Complete Job Flow", test_complete_job_flow)
    ]

    try:
        passed = 0
        for name, test in tests:
            if run_test(name, test):
                passed += 1
        print(f"\nPassed {passed}/{len(tests)} seller endpoint tests")
    finally:
        cleanup_redis(r)

if __name__ == "__main__":
    run_seller_tests()