"""
Tests for chat endpoints:
- Sending messages
- Reading messages
"""

import requests, time
from conftest import run_test

def test_send_message(api_url, test_state):
    """Test sending a chat message"""
    if not test_state.buyer_token:
        return False, "No buyer token available"
        
    headers = {"Authorization": f"Bearer {test_state.buyer_token}"}
    chat_data = {
        "username": test_state.buyer_username,
        "recipient": test_state.seller_username,
        "message": "Test message",
        "password": "password123"
    }
    
    response = requests.post(f"{api_url}/chat",
                          json=chat_data,
                          headers=headers)
    
    if response.status_code != 200:
        return False, f"Message send failed: {response.status_code}"
        
    return True, "Message sent successfully"

def test_get_messages(api_url, test_state):
    """Test retrieving chat messages"""
    if not test_state.seller_token:
        return False, "No seller token available"
        
    headers = {"Authorization": f"Bearer {test_state.seller_token}"}
    get_data = {
        "username": test_state.seller_username,
        "password": "password123"
    }
    
    response = requests.get(f"{api_url}/chat",
                         headers=headers,
                         json=get_data)
    
    if response.status_code != 200:
        return False, f"Message retrieval failed: {response.status_code}"
        
    messages = response.json().get('messages', [])
    if not messages:
        return False, "No messages found"
        
    return True, f"Retrieved {len(messages)} messages"

def test_message_validation(api_url, test_state):
    """Test message validation rules"""
    if not test_state.buyer_token:
        return False, "No buyer token available"
        
    headers = {"Authorization": f"Bearer {test_state.buyer_token}"}
    
    # Test too long message
    long_msg = "x" * 1001
    response = requests.post(f"{api_url}/chat",
                          json={
                              "username": test_state.buyer_username,
                              "recipient": test_state.seller_username,
                              "message": long_msg,
                              "password": "password123"
                          },
                          headers=headers)
                          
    if response.status_code != 400:
        return False, "Should reject too long message"
        
    return True, "Message validation working"

def run_messaging_tests(api_url, test_state):
    """Run all messaging tests"""
    tests = [
        ("Send Message", test_send_message, api_url, test_state),
        ("Get Messages", test_get_messages, api_url, test_state),
        ("Message Validation", test_message_validation, api_url, test_state)
    ]

    results = []
    for desc, test_func, *args in tests:
        results.append(run_test(desc, test_func, *args))
    
    return all(results)