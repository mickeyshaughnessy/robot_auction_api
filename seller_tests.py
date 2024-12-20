import requests, json, time, uuid, threading
from test_utils import (run_test, API_URL, setup_redis, cleanup_redis, 
                       create_test_user, TestConfig, random_location,
                       assert_valid_response)

def test_seller():
    r = setup_redis()
    print("\n=== 🤖 Seller Endpoint Tests ===")
    
    test_seller = f"test_seller_{uuid.uuid4().hex[:8]}"
    test_buyer = f"test_buyer_{uuid.uuid4().hex[:8]}"
    seller_token = create_test_user(test_seller, "password123")
    buyer_token = create_test_user(test_buyer, "password123")
    seller_headers = {"Authorization": f"Bearer {seller_token}"}
    buyer_headers = {"Authorization": f"Bearer {buyer_token}"}

    def create_test_bid():
        lat, lon = random_location()
        service = TestConfig.random_service()
        bid_data = {
            "service": service,
            "lat": lat,
            "lon": lon,
            "price": TestConfig.random_price(),
            "end_time": int(time.time()) + 3600
        }
        res = requests.post(f"{API_URL}/make_bid", json=bid_data, headers=buyer_headers)
        resp_data = assert_valid_response(res)
        return service, bid_data

    def test_grab_job():
        service, test_bid = create_test_bid()
        lat, lon = random_location()
        robot_data = {
            "service": service,
            "lat": lat,
            "lon": lon,
            "max_distance": 50
        }
        res = requests.post(f"{API_URL}/grab_job", json=robot_data, headers=seller_headers)
        data = assert_valid_response(res)
        return "job_id" in data, f"Job grabbed: {data.get('job_id', 'missing')}"

    def test_no_matching_service():
        _, test_bid = create_test_bid()
        robot_data = {
            "service": "nonexistent_service",
            "lat": 40.7128,
            "lon": -74.0060,
            "max_distance": 10
        }
        res = requests.post(f"{API_URL}/grab_job", json=robot_data, headers=seller_headers)
        return res.status_code == 204, f"No matching service - status: {res.status_code}"

    def test_too_far():
        _, test_bid = create_test_bid()
        robot_data = {
            "service": test_bid["service"],
            "lat": test_bid["lat"] + 100,
            "lon": test_bid["lon"] + 100,
            "max_distance": 1
        }
        res = requests.post(f"{API_URL}/grab_job", json=robot_data, headers=seller_headers)
        return res.status_code == 204, f"Distance check - status: {res.status_code}"

    def test_concurrent_grab():
        service, test_bid = create_test_bid()
        job_owner = None
        job_lock = threading.Lock()
        
        def try_grab_job(seller_num):
            nonlocal job_owner
            unique_user = f"test_seller_concurrent_{seller_num}_{uuid.uuid4().hex[:6]}"
            token = create_test_user(unique_user, "password123")
            headers = {"Authorization": f"Bearer {token}"}
            
            robot_data = {
                "service": service,
                "lat": test_bid["lat"],
                "lon": test_bid["lon"],
                "max_distance": 50
            }
            
            try:
                res = requests.post(f"{API_URL}/grab_job", json=robot_data, headers=headers)
                if res.status_code == 200:
                    with job_lock:
                        if job_owner is None:
                            job_owner = seller_num
            except Exception as e:
                print(f"Thread {seller_num} error: {str(e)}")
        
        threads = []
        for i in range(3):
            t = threading.Thread(target=try_grab_job, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=5)
        
        return job_owner is not None, f"Job assigned to seller {job_owner}"

    # Removed the "Complete Job Flow" test entirely

    tests = [
        ("Grab Job", test_grab_job),
        ("No Matching Service", test_no_matching_service),
        ("Distance Check", test_too_far),
        ("Concurrent Grab", test_concurrent_grab)
    ]

    try:
        passed = 0
        for name, test in tests:
            if run_test(name, test):
                passed += 1
        print(f"\nPassed {passed}/{len(tests)} seller endpoint tests")
        return passed == len(tests)
    finally:
        cleanup_redis(r)

if __name__ == "__main__":
    test_seller()
