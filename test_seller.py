"""
Tests for seller endpoints:
- Job grabbing
"""

import requests, hashlib
from conftest import run_test
import config

def test_grab_job(api_url, test_state):
    """Test job grabbing functionality"""
    if not test_state.seller_token:
        return False, "No seller token available"
        
    headers = {"Authorization": f"Bearer {test_state.seller_token}"}
    job_data = {
        "capabilities": "cleaning, gardening",
        "lat": 40.7128,
        "lon": -74.0060,
        "max_distance": 10,
        "seat": {
            "id": config.testrsx1.get("id"),
            "owner": config.testrsx1.get("owner"),
            "secret": hashlib.md5(config.testrsx1.get("phrase").encode()).hexdigest()
        }
    }
    
    response = requests.post(f"{api_url}/grab_job",
                          json=job_data,
                          headers=headers)
    
    if response.status_code == 200:
        resp_data = response.json()
        if not resp_data.get('job_id'):
            return False, "Missing job_id in response"
        test_state.test_job_id = resp_data['job_id']
        return True, f"Job grabbed: {test_state.test_job_id}"
    elif response.status_code == 204:
        return True, "No jobs available (expected)"
    
    return False, f"Job grab failed: {response.status_code}"

def test_invalid_seat(api_url, test_state):
    """Test job grabbing with invalid seat credentials"""
    if not test_state.seller_token:
        return False, "No seller token available"
        
    headers = {"Authorization": f"Bearer {test_state.seller_token}"}
    job_data = {
        "capabilities": "cleaning",
        "lat": 40.7128,
        "lon": -74.0060,
        "max_distance": 10,
        "seat": {
            "id": "invalid_id",
            "owner": "invalid_owner",
            "secret": "invalid_secret"
        }
    }
    
    response = requests.post(f"{api_url}/grab_job",
                          json=job_data,
                          headers=headers)
                          
    if response.status_code != 403:
        return False, f"Expected 403 for invalid seat, got {response.status_code}"
        
    return True, "Invalid seat properly rejected"

def run_seller_tests(api_url, test_state):
    """Run all seller endpoint tests"""
    tests = [
        ("Grab Job", test_grab_job, api_url, test_state),
        ("Invalid Seat", test_invalid_seat, api_url, test_state)
    ]

    results = []
    for desc, test_func, *args in tests:
        results.append(run_test(desc, test_func, *args))
    
    return all(results)