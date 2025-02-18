"""
Tests for shared endpoints:
- Nearby activity search
- Job signing
"""

import requests, time
from conftest import run_test

def test_nearby_activity(api_url, test_state):
    if not test_state.buyer_token:
        return False, "No buyer token available"
        
    headers = {"Authorization": f"Bearer {test_state.buyer_token}"}
    params = {
        "lat": 40.7128,
        "lon": -74.0060
    }
    
    response = requests.post(f"{api_url}/nearby", 
                          json=params,
                          headers=headers)
    
    if response.status_code != 200:
        return False, f"Nearby activity failed: {response.status_code}"
        
    bids = response.json().get('bids', {})
    return True, f"Found {len(bids)} nearby bids"

def test_sign_job(api_url, test_state):
    if not test_state.test_job_id:
        return False, "No job_id available to sign"
    
    # Test buyer signing
    response = requests.post(
        f"{api_url}/sign_job",
        headers={"Authorization": f"Bearer {test_state.buyer_token}"},
        json={
            "username": test_state.buyer_username,
            "job_id": test_state.test_job_id,
            "password": "password123",
            "star_rating": 5
        }
    )
    
    if response.status_code != 200:
        return False, f"Buyer signing failed: {response.status_code}"
    
    # Test seller signing
    response = requests.post(
        f"{api_url}/sign_job",
        headers={"Authorization": f"Bearer {test_state.seller_token}"},
        json={
            "username": test_state.seller_username,
            "job_id": test_state.test_job_id,
            "password": "password123",
            "star_rating": 4
        }
    )
    
    if response.status_code != 200:
        return False, f"Seller signing failed: {response.status_code}"
        
    return True, "Job signed by both parties"

def test_invalid_sign_job(api_url, test_state):
    headers = {"Authorization": f"Bearer {test_state.buyer_token}"}
    
    # Test invalid rating
    response = requests.post(
        f"{api_url}/sign_job",
        headers=headers,
        json={
            "username": test_state.buyer_username,
            "job_id": test_state.test_job_id,
            "password": "password123",
            "star_rating": 6  # Invalid rating
        }
    )
    
    if response.status_code != 400:
        return False, "Should reject invalid rating"
        
    return True, "Invalid cases handled correctly"

def run_shared_tests(api_url, test_state):
    """Run all shared endpoint tests"""
    tests = [
        ("Nearby Activity", test_nearby_activity, api_url, test_state),
        ("Sign Job", test_sign_job, api_url, test_state),
        ("Invalid Sign Job", test_invalid_sign_job, api_url, test_state)
    ]

    results = []
    for desc, test_func, *args in tests:
        results.append(run_test(desc, test_func, *args))
    
    return all(results)