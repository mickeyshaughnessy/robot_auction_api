"""
Tests for authentication endpoints and token validation:
- Registration
- Login 
- Token validation
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
    if not test_state.buyer_token:
        return False, "No token returned for buyer"
    
    # Test seller login
    response = requests.post(f"{api_url}/login", json={
        "username": test_state.seller_username,
        "password": "password123"
    })
    
    if response.status_code != 200:
        return False, f"Seller login failed: {response.status_code}"
        
    test_state.seller_token = response.json().get("access_token")
    if not test_state.seller_token:
        return False, "No token returned for seller"
    
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

def test_token_validation(api_url, test_state):
    """Test token validation on protected endpoints"""
    if not test_state.buyer_token:
        return False, "No token available for testing"
        
    # Test valid token
    headers = {"Authorization": f"Bearer {test_state.buyer_token}"}
    response = requests.get(f"{api_url}/account_data", headers=headers)
    print(f"Token validation response: {response.status_code} - {response.text}")
    if response.status_code != 200:
        return False, f"Valid token rejected with status {response.status_code}: {response.text}"
        
    # Test missing token
    response = requests.get(f"{api_url}/account_data")
    if response.status_code != 401:
        return False, "Missing token not caught"
        
    # Test invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{api_url}/account_data", headers=headers)
    if response.status_code != 401:
        return False, "Invalid token not caught"
        
    # Test malformed auth header
    headers = {"Authorization": "invalid_format"}
    response = requests.get(f"{api_url}/account_data", headers=headers)
    if response.status_code != 401:
        return False, "Malformed auth header not caught"
        
    return True, "Token validation tests passed"

def run_auth_tests(api_url, test_state):
    """Run all auth tests"""
    tests = [
        ("Registration", test_registration, api_url, test_state),
        ("Invalid Registration", test_invalid_registration, api_url),
        ("Login", test_login, api_url, test_state),
        ("Invalid Login", test_invalid_login, api_url),
        ("Token Validation", test_token_validation, api_url, test_state)
    ]

    results = []
    for desc, test_func, *args in tests:
        results.append(run_test(desc, test_func, *args))
    
    return all(results)