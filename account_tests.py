import requests, json, time, uuid
from test_utils import (run_test, API_URL, setup_redis, cleanup_redis, 
                       create_test_user, assert_valid_response)

def test_account():
    r = setup_redis()
    print("\n=== 👤 Account Management Tests ===")
    
    test_user = f"test_user_{uuid.uuid4().hex[:8]}"
    test_token = create_test_user(test_user, "password123")
    headers = {"Authorization": f"Bearer {test_token}"}

    def test_get_account_data():
        res = requests.get(f"{API_URL}/account_data", headers=headers)
        data = assert_valid_response(res)
        required_fields = ["created_on", "stars"]
        has_fields = all(field in data for field in required_fields)
        return has_fields, f"Account data fields present: {has_fields}"

    def test_get_account_no_auth():
        res = requests.get(f"{API_URL}/account_data")
        return res.status_code == 401, f"No auth check: {res.status_code}"

    def test_get_account_bad_token():
        bad_headers = {"Authorization": "Bearer bad_token"}
        res = requests.get(f"{API_URL}/account_data", headers=bad_headers)
        return res.status_code == 401, f"Bad token check: {res.status_code}"

    def test_account_star_rating_update():
        bid_data = {
            "service": "cleaning",
            "lat": 40.7128,
            "lon": -74.0060,
            "price": 50,
            "end_time": int(time.time()) + 3600
        }
        bid_res = requests.post(f"{API_URL}/make_bid", json=bid_data, headers=headers)
        assert_valid_response(bid_res)
        
        robot_data = {
            "services": "cleaning",
            "lat": 40.7128,
            "lon": -74.0060,
            "max_distance": 10
        }
        grab_res = requests.post(f"{API_URL}/grab_job", json=robot_data, headers=headers)
        job = assert_valid_response(grab_res)
        
        sign_data = {
            "job_id": job["job_id"],
            "password": "password123",
            "star_rating": 5
        }
        sign_res = requests.post(f"{API_URL}/sign_job", json=sign_data, headers=headers)
        assert_valid_response(sign_res)
        
        res = requests.get(f"{API_URL}/account_data", headers=headers)
        data = assert_valid_response(res)
        has_new_rating = data["stars"] > 0
        return has_new_rating, f"Star rating updated: {data['stars']}"

    def test_account_data_readonly():
        data = {"stars": 100}
        res = requests.post(f"{API_URL}/account_data", json=data, headers=headers)
        return res.status_code in [405, 404], f"Read-only check: {res.status_code}"

    tests = [
        ("Get Account Data", test_get_account_data),
        ("Account No Auth", test_get_account_no_auth),
        ("Account Bad Token", test_get_account_bad_token),
        ("Star Rating Update", test_account_star_rating_update),
        ("Account Data Readonly", test_account_data_readonly)
    ]

    try:
        passed = 0
        for name, test in tests:
            if run_test(name, test):
                passed += 1
        print(f"\nPassed {passed}/{len(tests)} account management tests")
    finally:
        cleanup_redis(r)

if __name__ == "__main__":
    test_account()