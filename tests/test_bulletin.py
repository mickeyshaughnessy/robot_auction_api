"""
Tests for bulletin board endpoints:
- Posting bulletins
- Reading bulletins
"""

import requests
from conftest import run_test

def test_post_bulletin(api_url, test_state):
    """Test posting a bulletin"""
    if not test_state.buyer_token:
        return False, "No buyer token available"
        
    headers = {"Authorization": f"Bearer {test_state.buyer_token}"}
    bulletin_data = {
        "username": test_state.buyer_username,
        "password": "password123",
        "title": "Test Bulletin",
        "content": "Test content",
        "category": "announcement"
    }
    
    response = requests.post(f"{api_url}/bulletin",
                          json=bulletin_data,
                          headers=headers)
    
    if response.status_code != 200:
        return False, f"Bulletin post failed: {response.status_code}"
        
    return True, "Bulletin posted successfully"

def test_get_bulletins(api_url, test_state):
    """Test retrieving bulletins"""
    if not test_state.buyer_token:
        return False, "No buyer token available"
        
    headers = {"Authorization": f"Bearer {test_state.buyer_token}"}
    
    # Test getting all bulletins
    response = requests.get(f"{api_url}/bulletin",
                         headers=headers)
    
    if response.status_code != 200:
        return False, f"Bulletin retrieval failed: {response.status_code}"
        
    bulletins = response.json().get('bulletins', [])
    if not bulletins:
        return False, "No bulletins found"
        
    # Test category filter
    response = requests.get(f"{api_url}/bulletin",
                         params={"category": "announcement"},
                         headers=headers)
    
    if response.status_code != 200:
        return False, f"Category filter failed: {response.status_code}"
        
    return True, "Bulletin retrieval tests passed"

def test_bulletin_validation(api_url, test_state):
    """Test bulletin validation rules"""
    if not test_state.buyer_token:
        return False, "No buyer token available"
        
    headers = {"Authorization": f"Bearer {test_state.buyer_token}"}
    
    test_cases = [
        ({
            "username": test_state.buyer_username,
            "password": "password123",
            "title": "x" * 101,  # Too long title
            "content": "Test"
        }, "Title too long"),
        ({
            "username": test_state.buyer_username,
            "password": "password123",
            "title": "Test",
            "content": "x" * 2001  # Too long content
        }, "Content too long")
    ]
    
    for data, case in test_cases:
        response = requests.post(f"{api_url}/bulletin",
                              json=data,
                              headers=headers)
        if response.status_code != 400:
            return False, f"Expected 400 for {case}"
            
    return True, "Bulletin validation tests passed"

def run_bulletin_tests(api_url, test_state):
    """Run all bulletin board tests"""
    tests = [
        ("Post Bulletin", test_post_bulletin, api_url, test_state),
        ("Get Bulletins", test_get_bulletins, api_url, test_state),
        ("Bulletin Validation", test_bulletin_validation, api_url, test_state)
    ]

    results = []
    for desc, test_func, *args in tests:
        results.append(run_test(desc, test_func, *args))
    
    return all(results)