"""
Tests for core utilities
"""

from utils import calculate_distance, hash_password, verify_password
from conftest import run_test

def test_distance_calculation():
    """Test distance calculations"""
    # NYC to LA coordinates
    nyc = (40.7128, -74.0060)
    la = (34.0522, -118.2437)
    distance = calculate_distance(nyc, la)
    
    # Should be ~2450 miles
    expected = 2450
    margin = 50  # Allow 50 mile margin of error
    
    if not (expected - margin <= distance <= expected + margin):
        return False, f"Distance {distance} not within expected range"
        
    return True, "Distance calculation works"

def test_password_hashing():
    """Test password hashing and verification"""
    password = "testpassword123"
    
    # Hash password
    hashed = hash_password(password)
    if not hashed or len(hashed) < 20:  # Basic length check
        return False, "Invalid hash generated"
        
    # Verify correct password
    if not verify_password(hashed, password):
        return False, "Failed to verify correct password"
        
    # Verify wrong password fails
    if verify_password(hashed, "wrongpassword"):
        return False, "Verified wrong password"
        
    return True, "Password hashing works"

def run_util_tests():
    """Run all utility tests"""
    tests = [
        ("Distance Calculation", test_distance_calculation),
        ("Password Hashing", test_password_hashing)
    ]

    results = []
    for desc, test_func in tests:
        results.append(run_test(desc, test_func))
    
    return all(results)