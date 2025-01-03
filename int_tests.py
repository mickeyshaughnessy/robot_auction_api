import requests
import json
import time
from utils import setup_redis, cleanup_redis
import config
import uuid

API_URL = config.API_URL

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
    r = setup_redis(config.REDIS_HOST, config.REDIS_PORT, config.REDIS_DB)
    cleanup_redis(r)

    # Generate unique usernames
    test_buyer_username = f"test_buyer_{uuid.uuid4().hex[:8]}"
    test_seller_username = f"test_seller_{uuid.uuid4().hex[:8]}"

    # Tokens to be used across tests
    buyer_token = None
    seller_token = None

    test_results = []

    try:
        def test_ping():
            response = requests.get(f"{API_URL}/ping")
            success = response.status_code == 200
            message = f"Ping status: {response.status_code}"
            return success, message

        def test_buyer_registration():
            response = requests.post(f"{API_URL}/register", json={"username": test_buyer_username, "password": "password"})
            success = response.status_code == 201
            message = f"Buyer registration status: {response.status_code}, Response: {response.text}"
            return success, message

        def test_seller_registration():
            response = requests.post(f"{API_URL}/register", json={"username": test_seller_username, "password": "password"})
            success = response.status_code == 201
            message = f"Seller registration status: {response.status_code}, Response: {response.text}"
            return success, message

        def test_buyer_login():
            nonlocal buyer_token
            response = requests.post(f"{API_URL}/login", json={"username": test_buyer_username, "password": "password"})
            if response.status_code == 200:
                buyer_token = response.json().get("access_token")
            success = response.status_code == 200 and buyer_token is not None
            message = f"Buyer login: {'🔑 Token received' if buyer_token else '🚫 No token'}, Status: {response.status_code}"
            return success, message

        def test_seller_login():
            nonlocal seller_token
            response = requests.post(f"{API_URL}/login", json={"username": test_seller_username, "password": "password"})
            if response.status_code == 200:
                seller_token = response.json().get("access_token")
            success = response.status_code == 200 and seller_token is not None
            message = f"Seller login: {'🔑 Token received' if seller_token else '🚫 No token'}, Status: {response.status_code}"
            return success, message

        def test_multiple_bid_submissions():
            if not buyer_token:
                return False, "Buyer token not available. Cannot submit bids."
            services = ["cleaning", "gardening", "pet_sitting"]
            results = []
            headers = {"Authorization": f"Bearer {buyer_token}"}
            for simulated in [True, False]:
                bid_ids = []
                for service in services:
                    bid_data = {
                        "service": service,
                        "lat": 40.7128,
                        "lon": -74.0060,
                        "price": 50,
                        "end_time": int(time.time()) + 3600
                    }
                    if simulated:
                        bid_data["simulated"] = config.SIMULATION_KEY
                    response = requests.post(f"{API_URL}/make_bid", json=bid_data, headers=headers)
                    if response.status_code != 200:
                        return False, f"{'Simulated' if simulated else 'Production'} bid submission failed for {service}: status {response.status_code}, Response: {response.text}"
                    bid_ids.append(response.json().get('bid_id'))
                results.append(f"{'🎮 Simulated' if simulated else '🏭 Production'}: {len(bid_ids)} bids placed")
            return True, " | ".join(results)

        def test_nearby_activity():
            if not buyer_token:
                return False, "Buyer token not available. Cannot check nearby activity."
            results = []
            headers = {"Authorization": f"Bearer {buyer_token}"}
            for simulated in [True, False]:
                data = {"lat": 40.7128, "lon": -74.0060}
                if simulated:
                    data["simulated"] = config.SIMULATION_KEY
                response = requests.post(f"{API_URL}/nearby", json=data, headers=headers)
                if response.status_code != 200:
                    return False, f"Nearby activity request failed: status {response.status_code}, Response: {response.text}"
                api_bids = response.json()
                all_bids = r.hgetall(config.REDHASH_SIMULATED_ALL_LIVE_BIDS if simulated else config.REDHASH_ALL_LIVE_BIDS)
                results.append(f"{'🎮 Simulated' if simulated else '🏭 Production'}: API returned {len(api_bids)} bids, Redis has {len(all_bids)} bids")
            return True, " | ".join(results)

        def test_grab_job():
            if not seller_token:
                return False, "Seller token not available. Cannot grab jobs."
            results = []
            headers = {"Authorization": f"Bearer {seller_token}"}
            for simulated in [True, False]:
                robot_data = {
                    "capabilities": "cleaning, gardening",
                    "lat": 40.7128,
                    "lon": -74.0060,
                    "max_distance": 10
                }
                if simulated:
                    robot_data["simulated"] = config.SIMULATION_KEY
                response = requests.post(f"{API_URL}/grab_job", json=robot_data, headers=headers)
                status = "🤖 Job grabbed" if response.status_code == 200 else f"🚫 No job available (status code {response.status_code}, Response: {response.text})"
                results.append(f"{'🎮 Simulated' if simulated else '🏭 Production'}: {status}")
            return True, " | ".join(results)

        def test_sign_job():
            if not buyer_token or not seller_token:
                return False, "Buyer or Seller token not available. Cannot sign jobs."
            results = []
            buyer_headers = {"Authorization": f"Bearer {buyer_token}"}
            seller_headers = {"Authorization": f"Bearer {seller_token}"}
            for simulated in [True, False]:
                # Create a bid
                bid_data = {
                    "service": "cleaning",
                    "lat": 40.7128,
                    "lon": -74.0060,
                    "price": 50,
                    "end_time": int(time.time()) + 3600
                }
                if simulated:
                    bid_data["simulated"] = config.SIMULATION_KEY
                bid_response = requests.post(f"{API_URL}/make_bid", json=bid_data, headers=buyer_headers)
                if bid_response.status_code != 200:
                    return False, f"Failed to create {'simulated' if simulated else 'production'} bid: {bid_response.status_code}, Response: {bid_response.text}"

                # Grab the job
                robot_data = {
                    "capabilities": "cleaning",
                    "lat": 40.7128,
                    "lon": -74.0060,
                    "max_distance": 10
                }
                if simulated:
                    robot_data["simulated"] = config.SIMULATION_KEY
                grab_response = requests.post(f"{API_URL}/grab_job", json=robot_data, headers=seller_headers)
                if grab_response.status_code != 200:
                    return False, f"Failed to grab job: status {grab_response.status_code}, Response: {grab_response.text}"

                job_id = grab_response.json().get('job_id')
                if not job_id:
                    return False, f"No job ID returned in grab_job response: {grab_response.text}"

                # Buyer signs the job
                buyer_sign_data = {
                    "job_id": job_id,
                    "password": "password",
                    "star_rating": 5
                }
                if simulated:
                    buyer_sign_data["simulated"] = config.SIMULATION_KEY
                buyer_sign_response = requests.post(f"{API_URL}/sign_job", json=buyer_sign_data, headers=buyer_headers)
                buyer_success = buyer_sign_response.status_code == 200

                # Seller signs the job
                seller_sign_data = {
                    "job_id": job_id,
                    "password": "password",
                    "star_rating": 4
                }
                if simulated:
                    seller_sign_data["simulated"] = config.SIMULATION_KEY
                seller_sign_response = requests.post(f"{API_URL}/sign_job", json=seller_sign_data, headers=seller_headers)
                seller_success = seller_sign_response.status_code == 200

                results.append(f"{'🎮 Simulated' if simulated else '🏭 Production'}: Buyer {'✅' if buyer_success else '❌'}, Seller {'✅' if seller_success else '❌'}")
            return True, " | ".join(results)

        def test_send_chat():
            if not buyer_token or not seller_token:
                return False, "Buyer or Seller token not available. Cannot test chat."
            
            buyer_headers = {"Authorization": f"Bearer {buyer_token}"}
            
            # Test sending a message from buyer to seller
            message_data = {
                "recipient": test_seller_username,
                "message": "Hey, quick question about the cleaning service!",
                "password": "password"
            }
            
            response = requests.post(f"{API_URL}/chat", json=message_data, headers=buyer_headers)
            if response.status_code != 200:
                return False, f"Failed to send chat message: status {response.status_code}, Response: {response.text}"
            
            message_id = response.json().get('message_id')
            if not message_id:
                return False, "No message ID returned in send_chat response"
                
            return True, f"💬 Message sent successfully with ID: {message_id}"
        
        def test_get_chat():
            if not seller_token:
                return False, "Seller token not available. Cannot test chat retrieval."
                
            seller_headers = {"Authorization": f"Bearer {seller_token}"}
            
            # Get chat messages for seller
            get_data = {"password": "password"}
            response = requests.get(f"{API_URL}/chat", json=get_data, headers=seller_headers)
            
            if response.status_code != 200:
                return False, f"Failed to get chat messages: status {response.status_code}, Response: {response.text}"
                
            messages = response.json().get('messages', [])
            message_count = len(messages)
            
            # Verify message structure
            if message_count > 0:
                first_msg = messages[0]
                required_fields = ['id', 'sender', 'recipient', 'message', 'timestamp']
                if not all(field in first_msg for field in required_fields):
                    return False, f"❌ Message missing required fields. Found: {list(first_msg.keys())}"
                    
            return True, f"📨 Retrieved {message_count} messages successfully"

        def test_post_bulletin():
            if not buyer_token:
                return False, "Buyer token not available. Cannot test bulletin posting."
            
            buyer_headers = {"Authorization": f"Bearer {buyer_token}"}
            
            # Test posting a bulletin
            bulletin_data = {
                "title": "Test Announcement",
                "content": "This is a test bulletin post.",
                "category": "announcement",
                "password": "password"
            }
            
            response = requests.post(f"{API_URL}/bulletin", json=bulletin_data, headers=buyer_headers)
            if response.status_code != 200:
                return False, f"Failed to post bulletin: status {response.status_code}, Response: {response.text}"
            
            bulletin_id = response.json().get('bulletin_id')
            if not bulletin_id:
                return False, "No bulletin ID returned in response"
                
            return True, f"📢 Bulletin posted successfully with ID: {bulletin_id}"
        
        def test_get_bulletins():
            if not seller_token:
                return False, "Seller token not available. Cannot test bulletin retrieval."
                
            seller_headers = {"Authorization": f"Bearer {seller_token}"}
            
            # Test different category filters
            categories = ['announcement', None]
            results = []
            
            for category in categories:
                params = {'limit': 5}
                if category:
                    params['category'] = category
                    
                response = requests.get(f"{API_URL}/bulletin", params=params, headers=seller_headers)
                if response.status_code != 200:
                    return False, f"Failed to get bulletins: status {response.status_code}, Response: {response.text}"
                    
                bulletins = response.json().get('bulletins', [])
                filter_text = f"category '{category}'" if category else "all categories"
                results.append(f"{filter_text}: {len(bulletins)} posts")
            
            return True, f"📋 Retrieved bulletins - " + " | ".join(results)

        tests = [
            ("Ping", test_ping),
            ("Buyer Registration", test_buyer_registration),
            ("Seller Registration", test_seller_registration),
            ("Buyer Login", test_buyer_login),
            ("Seller Login", test_seller_login),
            ("Multiple Bid Submissions", test_multiple_bid_submissions),
            ("Nearby Activity", test_nearby_activity),
            ("Grab Job", test_grab_job),
            ("Sign Job", test_sign_job),
            ("Send Chat", test_send_chat),
            ("Get Chat", test_get_chat),
            ("Post Bulletin", test_post_bulletin),
            ("Get Bulletins", test_get_bulletins),
        ]

        total_tests = len(tests)
        passed_tests = 0

        for description, test in tests:
            result = run_test(description, test)
            if result:
                passed_tests += 1
            test_results.append((description, result))

    finally:
        cleanup_redis(r)

    # Test Summary
    print("\n..``..\033[1m🏁 Test Summary 🏁\033[0m..``..")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")

if __name__ == "__main__":
    run_tests()
