"""
Tests for buyer endpoints:
- Bid submission
"""

import requests, time
from conftest import run_test

def test_make_bid(api_url, test_state):
    if not test_state.buyer_token:
        return False, "No buyer token available"
    
    headers = {"Authorization": f"Bearer {test_state.buyer_token}"}
    bid_data = {
        "service": "cleaning",
        "lat": 40.7128,
        "lon": -74.0060,
        "price": 50,
        "end_time": int(time.time()) + 3600
    }
    
    response = requests.post(f"{api_url}/make_bid", 
                          json=bid_data, 
                          headers=headers)
    
    if response.status_code != 200:
        return False, f"Bid creation failed: {response.status_code}"
        
    resp_data = response.json()
    if not resp_data.get('bid_id'):
        return False, "Missing bid_id in response"
        
    test_state.test_bid_id = resp_data['bid_id']
    return True, f"Bid created: {test_state.test_bid_id}"

def test_invalid_bid(api_url, test_state):
    if not test_state.buyer_token:
        return False, "No buyer token available"
    
    headers = {"Authorization": f"Bearer {test_state.buyer_token}"}
    bid_data = {
        "service": "cleaning"
        # Missing required fields
    }
    
    response = requests.post(f"{api_url}/make_bid", 
                          json=bid_data, 
                          headers=headers)
    
    if response.status_code != 400:
        return False, f"Expected 400 for invalid bid, got {response.status_code}"
    
    return True, "Invalid bid properly rejected"

def run_buyer_tests(api_url, test_state):
    """Run all buyer endpoint tests"""
    tests = [
        ("Make Bid", test_make_bid, api_url, test_state),
        ("Invalid Bid", test_invalid_bid, api_url, test_state)
    ]

    results = []
    for desc, test_func, *args in tests:
        results.append(run_test(desc, test_func, *args))
    
    return all(results)