"""
Main test runner for Robot Services Exchange API
"""

from conftest import TestState
from test_auth import run_auth_tests
from test_buyer import run_buyer_tests
from test_seller import run_seller_tests
from test_shared import run_shared_tests
from test_messaging import run_messaging_tests
from test_bulletin import run_bulletin_tests
from test_utils import run_util_tests
import config

def run_all_tests():
    """Run all test suites in order"""
    test_state = TestState()
    api_url = config.API_URL
    
    test_suites = [
        ("Auth Tests", run_auth_tests),
        ("Utils Tests", run_util_tests),
        ("Buyer Tests", run_buyer_tests),
        ("Seller Tests", run_seller_tests),
        ("Shared Tests", run_shared_tests),
        ("Messaging Tests", run_messaging_tests),
        ("Bulletin Tests", run_bulletin_tests)
    ]

    results = []
    for name, test_suite in test_suites:
        print(f"\n{'=' * 50}")
        print(f"Running {name}")
        print(f"{'=' * 50}")
        result = test_suite(api_url, test_state)
        results.append((name, result))

    # Print summary
    print("\n🏁 Test Summary")
    print("=" * 50)
    passed = sum(1 for _, result in results if result)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")

    print(f"\nPassed: {passed}/{len(results)}")
    
if __name__ == "__main__":
    run_all_tests()