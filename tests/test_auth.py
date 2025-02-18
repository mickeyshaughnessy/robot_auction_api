"""
Authentication tests for Robot Services Exchange API 
"""
import requests
import uuid
from conftest import TestState

def run_auth_tests(api_url: str, test_state: TestState) -> bool:
    """
    Run authentication test suite and set up test users
    
    Args:
        api_url: Base API URL
        test_state: Shared test state object
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    try:
        # Create buyer account
        buyer_username = f"test_buyer_{uuid.uuid4().hex[:8]}"
        buyer_data = {"username": buyer_username, "password": "password123"}
        r = requests.post(f"{api_url}/register", json=buyer_data)
        assert r.status_code == 201, f"Buyer registration failed: {r.text}"
        print("✅ Registration successful")

        # Create seller account
        seller_username = f"test_seller_{uuid.uuid4().hex[:8]}"
        seller_data = {"username": seller_username, "password": "password123"}
        r = requests.post(f"{api_url}/register", json=seller_data)
        assert r.status_code == 201, f"Seller registration failed: {r.text}"

        # Login as buyer
        r = requests.post(f"{api_url}/login", json=buyer_data)
        assert r.status_code == 200, f"Buyer login failed: {r.text}"
        buyer_token = r.json()["access_token"]
        
        # Login as seller
        r = requests.post(f"{api_url}/login", json=seller_data)
        assert r.status_code == 200, f"Seller login failed: {r.text}"
        seller_token = r.json()["access_token"]
        print("✅ Login successful")

        # Test protected endpoint access with buyer token
        headers = {"Authorization": f"Bearer {buyer_token}"}
        r = requests.get(f"{api_url}/account_data", headers=headers)
        assert r.status_code == 200, "Protected endpoint access failed"
        print("✅ Protected endpoint access successful")

        # Store BOTH buyer and seller credentials in test state
        test_state.buyer_token = buyer_token
        test_state.seller_token = seller_token
        test_state.buyer_username = buyer_username
        test_state.seller_username = seller_username
        test_state.password = "password123"  # Store shared password

        return True

    except Exception as e:
        print(f"❌ AUTH TEST FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    from test_utils import API_URL
    test_state = TestState()
    success = run_auth_tests(API_URL, test_state)
    print(f"\nAuth Tests: {'✅ PASS' if success else '❌ FAIL'}")