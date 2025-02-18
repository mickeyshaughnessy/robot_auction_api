"""
Test configuration and shared test utilities
"""

import uuid
import config

class TestState:
    """Minimal test state management"""
    def __init__(self):
        self.buyer_username = f"test_buyer_{uuid.uuid4().hex[:8]}"
        self.seller_username = f"test_seller_{uuid.uuid4().hex[:8]}"
        self.buyer_token = None
        self.seller_token = None
        self.test_bid_id = None
        self.test_job_id = None

def run_test(description, test_function, *args):
    """Run a test with consistent formatting"""
    print(f"\nTesting: {description}")
    try:
        result, message = test_function(*args)
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {message}")
        return result
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False