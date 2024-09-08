import requests, json, time
from utils import setup_redis, cleanup_redis
import config

API_URL = f"http://{config.API_HOST}:{config.API_PORT}"

def run_test(description, test_function, *args):
    print(f"\n{'*' * 40}")
    print(f"🧪 Testing: {description}")
    print(f"{'*' * 40}")
    try:
        result, message = test_function(*args)
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {message}")
        return result
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def run_tests():
    r, buyer_token, seller_token = setup_redis(config.REDIS_HOST, config.REDIS_PORT, config.REDIS_DB), None, None
    cleanup_redis(r)

    try:
        def test_ping():
            response = requests.get(f"{API_URL}/ping")
            return response.status_code == 200, f"Ping status: {response.status_code}"

        def test_buyer_registration():
            response = requests.post(f"{API_URL}/register", json={"username": "test_buyer", "password": "password", "user_type": "buyer"})
            return response.status_code == 201, f"Buyer registration status: {response.status_code}"

        def test_seller_registration():
            response = requests.post(f"{API_URL}/register", json={"username": "test_seller", "password": "password", "user_type": "seller"})
            return response.status_code == 201, f"Seller registration status: {response.status_code}"

        def test_buyer_login():
            nonlocal buyer_token
            response = requests.post(f"{API_URL}/login", json={"username": "test_buyer", "password": "password"})
            if response.status_code == 200:
                buyer_token = response.json().get("access_token")
            return response.status_code == 200, f"Buyer login: {'🔑 Token received' if buyer_token else '🚫 No token'}"

        def test_seller_login():
            nonlocal seller_token
            response = requests.post(f"{API_URL}/login", json={"username": "test_seller", "password": "password"})
            if response.status_code == 200:
                seller_token = response.json().get("access_token")
            return response.status_code == 200, f"Seller login: {'🔑 Token received' if seller_token else '🚫 No token'}"

        def test_multiple_bid_submissions():
            services = ["cleaning", "gardening", "pet_sitting"]
            results = []
            for simulated in [True, False]:
                bid_ids = []
                for service in services:
                    bid_data = {
                        "service": service,
                        "lat": 40.7128,
                        "lon": -74.0060,
                        "price": 50,
                        "end_time": int(time.time()) + 3600,
                        "simulated": simulated
                    }
                    response = requests.post(f"{API_URL}/make_bid", json=bid_data, headers={"Authorization": f"Bearer {buyer_token}"})
                    if response.status_code != 200:
                        return False, f"{'Simulated' if simulated else 'Production'} bid submission failed for {service}: status {response.status_code}"
                    bid_ids.append(response.json().get('bid_id'))
                results.append(f"{'🎮 Simulated' if simulated else '🏭 Production'}: {len(bid_ids)} bids placed")
            return True, " | ".join(results)

        def test_nearby_activity():
            results = []
            for simulated in [True, False]:
                data = {"lat": 40.7128, "lon": -74.0060, "simulated": simulated}
                response = requests.post(f"{API_URL}/nearby", json=data, headers={"Authorization": f"Bearer {buyer_token}"})
                all_bids = r.hgetall(config.REDHASH_SIMULATED_ALL_LIVE_BIDS if simulated else config.REDHASH_ALL_LIVE_BIDS)
                results.append(f"{'🎮 Simulated' if simulated else '🏭 Production'}: API: {len(response.json())}, Redis: {len(all_bids)}")
            return True, " | ".join(results)

        def test_grab_job():
            results = []
            for simulated in [True, False]:
                robot_data = {"service": "cleaning, gardening", "lat": 40.7128, "lon": -74.0060, "max_distance": 10, "simulated": simulated}
                response = requests.post(f"{API_URL}/grab_job", json=robot_data, headers={"Authorization": f"Bearer {seller_token}"})
                status = "🤖 Job grabbed" if response.status_code == 200 else "🚫 No job available"
                results.append(f"{'🎮 Simulated' if simulated else '🏭 Production'}: {status}")
            return True, " | ".join(results)

        def test_sign_job():
            results = []
            for simulated in [True, False]:
                bid_data = {
                    "service": "cleaning", "lat": 40.7128, "lon": -74.0060, "price": 50, "end_time": int(time.time()) + 3600,
                    "simulated": simulated
                }
                bid_response = requests.post(f"{API_URL}/make_bid", json=bid_data, headers={"Authorization": f"Bearer {buyer_token}"})
                if bid_response.status_code != 200:
                    return False, f"Failed to create {'simulated' if simulated else 'production'} bid for sign_job test: {bid_response.status_code}"

                robot_data = {"service": "cleaning", "lat": 40.7128, "lon": -74.0060, "max_distance": 10, "simulated": simulated}
                grab_response = requests.post(f"{API_URL}/grab_job", json=robot_data, headers={"Authorization": f"Bearer {seller_token}"})
                if grab_response.status_code != 200:
                    return False, f"Failed to grab {'simulated' if simulated else 'production'} job for sign_job test: {grab_response.status_code}"

                job_id = grab_response.json().get('job_id')

                buyer_sign_data = {"username": "test_buyer", "job_id": job_id, "password": "password", "star_rating": 5, "simulated": simulated}
                seller_sign_data = {"username": "test_seller", "job_id": job_id, "password": "password", "star_rating": 4, "simulated": simulated}

                buyer_sign_response = requests.post(f"{API_URL}/sign_job", json=buyer_sign_data, headers={"Authorization": f"Bearer {buyer_token}"})
                seller_sign_response = requests.post(f"{API_URL}/sign_job", json=seller_sign_data, headers={"Authorization": f"Bearer {seller_token}"})

                results.append(f"{'🎮 Simulated' if simulated else '🏭 Production'}: Buyer {'✅' if buyer_sign_response.status_code == 200 else '❌'}, Seller {'✅' if seller_sign_response.status_code == 200 else '❌'}")
            return True, " | ".join(results)

        tests = [test_ping, test_buyer_registration, test_seller_registration, test_buyer_login, test_seller_login,
                 test_multiple_bid_submissions, test_nearby_activity, test_grab_job, test_sign_job]

        for test in tests:
            run_test(test.__name__.replace('test_', '').replace('_', ' ').capitalize(), test)

    finally:
        cleanup_redis(r)

    print("\n..``..\033[1m🏁 Test Summary 🏁\033[0m..``..")
    print(f"Total tests: {len(tests)}")
    passed_tests = sum(1 for test in tests if run_test(test.__name__.replace('test_', '').replace('_', ' ').capitalize(), test))
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(tests) - passed_tests}")

if __name__ == "__main__":
    run_tests()