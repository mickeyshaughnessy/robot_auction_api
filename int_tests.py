"""
🤔 Integration Tests for Robot Services Exchange (RSE) API
Key improvements:
- Uses proper auth headers throughout
- Matches API documentation endpoints
- Cleans up after each test
- Handles errors gracefully
- Uses shared state for test efficiency
"""

import requests, json, time, uuid, hashlib
from utils import setup_redis, cleanup_redis
import config

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

class TestState:
    """Shared state for tests to avoid repetitive setup"""
    def __init__(self):
        self.buyer_username = None
        self.seller_username = None
        self.buyer_token = None
        self.seller_token = None
        self.test_bid_id = None
        self.test_job_id = None
        self.redis = None
    
    def cleanup(self):
        if self.redis:
            cleanup_redis(self.redis)

def run_tests():
    """Main test runner with proper setup and cleanup"""
    state = TestState()
    state.redis = setup_redis(config.REDIS_HOST, config.REDIS_PORT, config.REDIS_DB)
    
    # Generate unique test usernames
    state.buyer_username = f"test_buyer_{uuid.uuid4().hex[:8]}"
    state.seller_username = f"test_seller_{uuid.uuid4().hex[:8]}"
    
    try:
        def test_ping():
            response = requests.get(f"{API_URL}/ping")
            return response.status_code == 200, f"Ping status: {response.status_code}"

        def test_buyer_registration():
            response = requests.post(f"{API_URL}/register", json={
                "username": state.buyer_username,
                "password": "password123"
            })
            return response.status_code == 201, f"Buyer registration: {response.status_code}"

        def test_seller_registration():
            response = requests.post(f"{API_URL}/register", json={
                "username": state.seller_username,
                "password": "password123"
            })
            return response.status_code == 201, f"Seller registration: {response.status_code}"

        def test_buyer_login():
            response = requests.post(f"{API_URL}/login", json={
                "username": state.buyer_username,
                "password": "password123"
            })
            if response.status_code == 200:
                state.buyer_token = response.json().get("access_token")
                return True, "Buyer login successful"
            return False, f"Buyer login failed: {response.status_code}"

        def test_seller_login():
            response = requests.post(f"{API_URL}/login", json={
                "username": state.seller_username,
                "password": "password123"
            })
            if response.status_code == 200:
                state.seller_token = response.json().get("access_token")
                return True, "Seller login successful"
            return False, f"Seller login failed: {response.status_code}"

        def test_make_bid():
            if not state.buyer_token:
                return False, "No buyer token available"
            
            headers = {"Authorization": f"Bearer {state.buyer_token}"}
            bid_data = {
                "service": "cleaning",
                "lat": 40.7128,
                "lon": -74.0060,
                "price": 50,
                "end_time": int(time.time()) + 3600
            }
            
            response = requests.post(f"{API_URL}/make_bid", 
                                  json=bid_data, 
                                  headers=headers)
            
            if response.status_code == 200:
                state.test_bid_id = response.json().get('bid_id')
                return True, f"Bid created: {state.test_bid_id}"
            return False, f"Bid creation failed: {response.status_code}"

        def test_nearby_activity():
            if not state.buyer_token:
                return False, "No buyer token available"
                
            headers = {"Authorization": f"Bearer {state.buyer_token}"}
            params = {
                "lat": 40.7128,
                "lon": -74.0060
            }
            
            response = requests.post(f"{API_URL}/nearby", 
                                  json=params,
                                  headers=headers)
            
            if response.status_code != 200:
                return False, f"Nearby activity failed: {response.status_code}"
                
            bids = response.json()
            return True, f"Found {len(bids)} nearby bids"

        def test_grab_job():
            if not state.seller_token:
                return False, "No seller token available"
                
            headers = {"Authorization": f"Bearer {state.seller_token}"}
            job_data = {
                "capabilities": "cleaning, gardening",  # Space after comma per docs
                "lat": 40.7128,
                "lon": -74.0060,
                "max_distance": 10,
                "seat": {
                    "id": config.testrsx1.get("id"),
                    "owner": config.testrsx1.get("owner"),
                    "secret": hashlib.md5(config.testrsx1.get("phrase").encode()).hexdigest()
                }
            }
            
            response = requests.post(f"{API_URL}/grab_job",
                                  json=job_data,
                                  headers=headers)
            
            if response.status_code == 200:
                state.test_job_id = response.json().get('job_id')
                return True, f"Job grabbed: {state.test_job_id}"
            elif response.status_code == 204:
                return True, "No jobs available (expected)"
            return False, f"Job grab failed: {response.status_code}"


        def test_sign_job():
            if not state.test_job_id:
                return False, "No job_id available to sign"
            
            test_cases = [
                {
                    "username": state.buyer_username,
                    "token": state.buyer_token,
                    "password": "password123",
                    "star_rating": 5
                },
                {
                    "username": state.seller_username, 
                    "token": state.seller_token,
                    "password": "password123",
                    "star_rating": 4
                }
            ]
            
            for case in test_cases:
                response = requests.post(
                    f"{API_URL}/sign_job",
                    headers={"Authorization": f"Bearer {case['token']}"},
                    json={
                        "username": case['username'],
                        "job_id": state.test_job_id,
                        "password": case['password'],
                        "star_rating": case['star_rating']
                    }
                )
                
                try:
                    resp_data = response.json()
                except ValueError:
                    return False, f"Invalid JSON response for {case['username']}"
                    
                # Consider both 200 and "already signed" as success cases
                if response.status_code == 200:
                    continue
                elif response.status_code == 400 and "already signed by this user" in resp_data.get("error", ""):
                    continue
                else:
                    return False, f"Signing failed for {case['username']}: {response.status_code} - {response.text}"
                    
            return True, "Job signatures verified for both parties"
        def test_chat():
            if not state.buyer_token:
                return False, "No buyer token available"
                
            headers = {"Authorization": f"Bearer {state.buyer_token}"}
            chat_data = {
                "recipient": state.seller_username,
                "message": "Test message",
                "password": "password123"  # Required per API docs
            }
            
            response = requests.post(f"{API_URL}/chat",
                                  json=chat_data,
                                  headers=headers)
            
            if response.status_code != 200:
                return False, f"Chat send failed: {response.status_code}"
                
            # Verify message received
            seller_headers = {"Authorization": f"Bearer {state.seller_token}"}
            get_response = requests.get(f"{API_URL}/chat",
                                     headers=seller_headers,
                                     json={"password": "password123"})
            
            if get_response.status_code != 200:
                return False, f"Chat retrieval failed: {get_response.status_code}"
                
            messages = get_response.json().get('messages', [])
            if not messages:
                return False, "No messages found"
                
            return True, f"Chat message sent and retrieved"

        def test_bulletin():
            if not state.buyer_token:
                return False, "No buyer token available"
                
            headers = {"Authorization": f"Bearer {state.buyer_token}"}
            bulletin_data = {
                "title": "Test Bulletin",
                "content": "Test content",
                "category": "announcement",
                "password": "password123"  # Required per API docs
            }
            
            post_response = requests.post(f"{API_URL}/bulletin",
                                       json=bulletin_data,
                                       headers=headers)
            
            if post_response.status_code != 200:
                return False, f"Bulletin post failed: {post_response.status_code}"
                
            # Verify bulletin visible
            get_response = requests.get(f"{API_URL}/bulletin",
                                     params={"category": "announcement"},
                                     headers=headers)
            
            if get_response.status_code != 200:
                return False, f"Bulletin retrieval failed: {get_response.status_code}"
                
            bulletins = get_response.json().get('bulletins', [])
            if not bulletins:
                return False, "No bulletins found"
                
            return True, "Bulletin posted and retrieved"

        # Test execution
        tests = [
            ("Ping", test_ping),
            ("Buyer Registration", test_buyer_registration),
            ("Seller Registration", test_seller_registration),
            ("Buyer Login", test_buyer_login),
            ("Seller Login", test_seller_login),
            ("Make Bid", test_make_bid),
            ("Nearby Activity", test_nearby_activity),
            ("Grab Job", test_grab_job),
            ("Sign Job", test_sign_job),
            ("Chat", test_chat),
            ("Bulletin", test_bulletin)
        ]

        total_tests = len(tests)
        passed_tests = sum(1 for desc, test in tests if run_test(desc, test))

        print("\n🏁 Test Summary 🏁")
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")

    finally:
        state.cleanup()

if __name__ == "__main__":
    run_tests()
