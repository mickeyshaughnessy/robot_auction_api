import requests, json, time, uuid
from test_utils import (run_test, API_URL, setup_redis, cleanup_redis, 
                        create_test_user, assert_valid_response)

def test_account():
    print("\n=== 👤 Account Management Tests ===")
    
    r = setup_redis()
    try:
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

        def test_account_data_readonly():
            data = {"stars": 100}
            res = requests.post(f"{API_URL}/account_data", json=data, headers=headers)
            return res.status_code in [405, 404], f"Read-only check: {res.status_code}"

        tests = [
            ("Get Account Data", test_get_account_data),
            ("Account No Auth", test_get_account_no_auth),
            ("Account Bad Token", test_get_account_bad_token),
            ("Account Data Readonly", test_account_data_readonly)
        ]

        passed = 0
        for name, test in tests:
            if run_test(name, test):
                passed += 1
        
        print(f"\nPassed {passed}/{len(tests)} account management tests")
        return passed == len(tests)
    except Exception as e:
        print(f"❌ EXCEPTION in test_account: {e}")
        return False
    finally:
        cleanup_redis(r)
