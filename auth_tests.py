import requests, json, time, uuid
from test_utils import run_test, API_URL, setup_redis, cleanup_redis, SIMULATION_KEY

def run_auth_tests():
    r = setup_redis()
    
    print("\n=== 🔒 Authentication Tests ===")
    test_results = []
    
    # Generate unique test usernames
    test_user = f"test_user_{uuid.uuid4().hex[:8]}"
    test_user2 = f"test_user_{uuid.uuid4().hex[:8]}"
    
    def test_register_success():
        res = requests.post(f"{API_URL}/register", json={
            "username": test_user,
            "password": "password123"
        })
        return res.status_code == 201, f"Registration: {res.status_code}"

    def test_register_duplicate():
        # First registration
        requests.post(f"{API_URL}/register", json={
            "username": test_user2,
            "password": "password123"
        })
        # Duplicate attempt
        res = requests.post(f"{API_URL}/register", json={
            "username": test_user2,
            "password": "password123"
        })
        return res.status_code == 400, f"Duplicate registration returned {res.status_code}"

    def test_register_invalid():
        res = requests.post(f"{API_URL}/register", json={
            "username": "a",  # Too short
            "password": "pass"  # Too short
        })
        return res.status_code == 400, f"Invalid registration: {res.status_code}"

    def test_login_success():
        res = requests.post(f"{API_URL}/login", json={
            "username": test_user,
            "password": "password123"
        })
        success = res.status_code == 200 and "access_token" in res.json()
        return success, f"Login success: {res.status_code}"

    def test_login_wrong_password():
        res = requests.post(f"{API_URL}/login", json={
            "username": test_user,
            "password": "wrongpass"
        })
        return res.status_code == 401, f"Wrong password: {res.status_code}"

    def test_login_nonexistent():
        res = requests.post(f"{API_URL}/login", json={
            "username": "nonexistent_user",
            "password": "password123"
        })
        return res.status_code == 401, f"Nonexistent user: {res.status_code}"

    def test_token_validation():
        # Get valid token
        res = requests.post(f"{API_URL}/login", json={
            "username": test_user,
            "password": "password123"
        })
        token = res.json()["access_token"]
        
        # Test with valid token
        res1 = requests.get(
            f"{API_URL}/account_data",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Test with invalid token
        res2 = requests.get(
            f"{API_URL}/account_data",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        # Test with missing token
        res3 = requests.get(f"{API_URL}/account_data")
        
        success = (res1.status_code == 200 and 
                  res2.status_code == 401 and 
                  res3.status_code == 401)
        
        return success, f"Token validation: {res1.status_code}, {res2.status_code}, {res3.status_code}"

    tests = [
        ("Register Success", test_register_success),
        ("Register Duplicate", test_register_duplicate),
        ("Register Invalid", test_register_invalid),
        ("Login Success", test_login_success),
        ("Login Wrong Password", test_login_wrong_password),
        ("Login Nonexistent", test_login_nonexistent),
        ("Token Validation", test_token_validation)
    ]

    try:
        passed = 0
        for name, test in tests:
            if run_test(name, test):
                passed += 1
            
        print(f"\nPassed {passed}/{len(tests)} authentication tests")
            
    finally:
        cleanup_redis(r)

if __name__ == "__main__":
    run_auth_tests()