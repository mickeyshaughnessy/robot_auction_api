"""
Tests for authentication endpoints:
- Registration
- Login 
"""

import requests
from conftest import run_test

def test_registration(api_url, test_state):
    """Test user registration"""
    response = requests.post(f"{api_url}/register", json={
        "username": test_state.buyer_username,
        "password": "password123"
    })
    
    if response.status_code != 201:
        return False, f"Registration failed: {response.status_code}"
    
    # Register seller account too
    response = requests.post(f"{api_url}/register", json={
        "username": test_state.seller_username,
        "password": "password123"
    })
    
    return response.status_code == 201, "Registration tests passed"

def test_invalid_registration(api_url):
    """Test invalid registration cases"""
    test_cases = [
        ({"username": "a", "password": "pass123"}, "Username too short"),
        ({"username": "user", "password": "123"}, "Password too short"),
        ({}, "Missing fields")
    ]
    
    for data, case in test_cases:
        response = requests.post(f"{api_url}/register", json=data)
        if response.status_code != 400:
            return False, f"Expected 400 for {case}"
            
    return True, "Invalid registration cases handled"

def test_login(api_url, test_state):
    """Test user login"""
    # Test buyer login
    response = requests.post(f"{api_url}/login", json={
        "username": test_state.buyer_username,
        "password": "password123"
    })
    
    if response.status_code != 200:
        return False, f"Buyer login failed: {response.status_code}"
        
    test_state.buyer_token = response.json().get("access_token")
    
    # Test seller login
    response = requests.post(f"{api_url}/login", json={
        "username": test_state.seller_username,
        "password": "password123"
    })
    
    if response.status_code != 200:
        return False, f"Seller login failed: {response.status_code}"
        
    test_state.seller_token = response.json().get("access_token")
    
    return True, "Login tests passed"

def test_invalid_login(api_url):
    """Test invalid login cases"""
    test_cases = [
        ({"username": "nonexistent", "password": "pass123"}, "User not found"),
        ({"username": "testuser", "password": "wrongpass"}, "Wrong password"),
        ({}, "Missing fields")
    ]
    
    for data, case in test_cases:
        response = requests.post(f"{api_url}/login", json=data)
        if response.status_code == 200:
            return False, f"Expected error for {case}"
            
    return True, "Invalid login cases handled"

def run_auth_tests(api_url, test_state):
    """Run all auth tests"""
    tests = [
        ("Registration", test_registration, api_url, test_state),
        ("Invalid Registration", test_invalid_registration, api_url),
        ("Login", test_login, api_url, test_state),
        ("Invalid Login", test_invalid_login, api_url)
    ]

    results = []
    for desc, test_func, *args in tests:
        results.append(run_test(desc, test_func, *args))
    
    return all(results)