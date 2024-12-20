import requests, json, uuid
from test_utils import API_URL

def test_auth():
    print("\n=== 🔐 Authentication Tests ===")
    try:
        # Test registration
        username = f"test_user_{uuid.uuid4().hex[:8]}"
        register_data = {"username": username, "password": "test123!"}

        r = requests.post(f"{API_URL}/register", json=register_data)
        print(f"Testing Registration - Status: {r.status_code}")
        assert r.status_code == 201, f"Registration failed: {r.text}"

        # Test login with wrong password
        wrong_login = {"username": username, "password": "wrong"}
        r = requests.post(f"{API_URL}/login", json=wrong_login)
        print(f"Testing: Login Wrong Password - Status: {r.status_code}")
        assert r.status_code == 401, "Wrong password should return 401"

        # Test login with correct password
        r = requests.post(f"{API_URL}/login", json=register_data)
        print(f"Testing: Login Correct - Status: {r.status_code}")
        assert r.status_code == 200, f"Login failed: {r.text}"
        token = r.json()["access_token"]

        # Test protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{API_URL}/account_data", headers=headers)
        print(f"Testing: Token Validation - Status: {r.status_code}")
        assert r.status_code == 200, "Token validation failed"

        return True  # All tests passed
    except AssertionError as e:
        print(f"❌ AUTH TEST FAILED: {e}")
        return False
