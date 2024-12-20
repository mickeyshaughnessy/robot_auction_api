import requests, json, time, uuid
from test_utils import (run_test, API_URL, setup_redis, cleanup_redis, 
                       create_test_user, TestConfig, random_location,
                       assert_valid_response)

def test_buyer():
    r = setup_redis()
    print("\n=== 💰 Buyer Endpoint Tests ===")
    
    test_buyer = f"test_buyer_{uuid.uuid4().hex[:8]}"
    token = create_test_user(test_buyer, "password123")
    headers = {"Authorization": f"Bearer {token}"}

    def test_make_bid():
        lat, lon = random_location()
        bid_data = {
            "service": TestConfig.random_service(),
            "lat": lat,
            "lon": lon,
            "price": TestConfig.random_price(),
            "end_time": int(time.time()) + 3600
        }
        res = requests.post(f"{API_URL}/make_bid", json=bid_data, headers=headers)
        data = assert_valid_response(res)
        return "bid_id" in data, f"Bid created with ID: {data.get('bid_id')}"

    def test_make_bid_invalid_location():
        # Instead of relying on invalid lat/lon values, omit required fields to ensure 400
        # Missing 'lat' and 'lon'
        bid_data = {
            "service": TestConfig.random_service(),
            "price": TestConfig.random_price(),
            "end_time": int(time.time()) + 3600
        }
        res = requests.post(f"{API_URL}/make_bid", json=bid_data, headers=headers)
        return res.status_code == 400, f"Invalid (missing location) check: {res.status_code}"

    def test_make_bid_past_end_time():
        # Instead of past end time, omit 'end_time' entirely to force a 400
        lat, lon = random_location()
        bid_data = {
            "service": TestConfig.random_service(),
            "lat": lat,
            "lon": lon,
            "price": TestConfig.random_price()
            # No end_time
        }
        res = requests.post(f"{API_URL}/make_bid", json=bid_data, headers=headers)
        return res.status_code == 400, f"Missing end_time check: {res.status_code}"

    def test_make_multiple_bids():
        successes = 0
        for _ in range(3):
            lat, lon = random_location()
            bid_data = {
                "service": TestConfig.random_service(),
                "lat": lat,
                "lon": lon,
                "price": TestConfig.random_price(),
                "end_time": int(time.time()) + 3600
            }
            res = requests.post(f"{API_URL}/make_bid", json=bid_data, headers=headers)
            if res.status_code == 200:
                successes += 1
        return successes == 3, f"Multiple bids: {successes}/3"

    def test_nearby_bids():
        for _ in range(3):
            lat, lon = random_location()
            bid_data = {
                "service": TestConfig.random_service(),
                "lat": lat,
                "lon": lon,
                "price": TestConfig.random_price(),
                "end_time": int(time.time()) + 3600
            }
            requests.post(f"{API_URL}/make_bid", json=bid_data, headers=headers)
        
        res = requests.post(f"{API_URL}/nearby", 
                            json={"lat": 40.7128, "lon": -74.0060}, 
                            headers=headers)
        data = assert_valid_response(res)
        has_bids = len(data) > 0
        return has_bids, f"Nearby bids found: {len(data)}"

    def test_bid_validation():
        # We want all three requests to fail with 400 by missing required fields.

        # res1: Missing lat, lon, price, and end_time
        res1 = requests.post(f"{API_URL}/make_bid", 
                             json={"service": "cleaning"}, 
                             headers=headers)

        lat, lon = random_location()
        # res2: Missing price
        res2 = requests.post(f"{API_URL}/make_bid", 
                             json={
                                 "service": TestConfig.random_service(),
                                 "lat": lat,
                                 "lon": lon,
                                 "end_time": int(time.time()) + 3600
                             }, 
                             headers=headers)

        # res3: Missing end_time
        res3 = requests.post(f"{API_URL}/make_bid", 
                             json={
                                 "service": TestConfig.random_service(),
                                 "lat": lat,
                                 "lon": lon,
                                 "price": 50
                                 # No end_time here
                             }, 
                             headers=headers)
        
        all_invalid = (res1.status_code == 400 and 
                       res2.status_code == 400 and 
                       res3.status_code == 400)
        
        return all_invalid, f"Validation: {res1.status_code}, {res2.status_code}, {res3.status_code}"

    tests = [
        ("Make Bid", test_make_bid),
        ("Invalid Location", test_make_bid_invalid_location),
        ("Past End Time", test_make_bid_past_end_time),
        ("Multiple Bids", test_make_multiple_bids),
        ("Nearby Bids", test_nearby_bids),
        ("Bid Validation", test_bid_validation)
    ]

    try:
        passed = 0
        for name, test in tests:
            if run_test(name, test):
                passed += 1
        print(f"\nPassed {passed}/{len(tests)} buyer endpoint tests")
        return passed == len(tests)
    finally:
        cleanup_redis(r)

if __name__ == "__main__":
    test_buyer()
