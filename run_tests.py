"""
Main test runner for Robot Services Exchange API
"""

from conftest import TestState
from tests.test_auth import run_auth_tests
from tests.test_buyer import run_buyer_tests
from tests.test_seller import run_seller_tests
from tests.test_shared import run_shared_tests
from tests.test_messaging import run_messaging_tests
from tests.test_bulletin import run_bulletin_tests
from tests.test_utils import run_util_tests
import config

def run_all_tests():
    """Run all test suites in order"""
    test_state = TestState()
    api_url = config.API_URL
    
    test_suites = [
        ("Auth Tests", run_auth_tests, True),
        ("Utils Tests", run_util_tests, False),
        ("Buyer Tests", run_buyer_tests, True),
        ("Seller Tests", run_seller_tests, True),
        ("Shared Tests", run_shared_tests, True),
        ("Messaging Tests", run_messaging_tests, True),
        ("Bulletin Tests", run_bulletin_tests, True)
    ]

    results = []
    for name, test_suite, needs_args in test_suites:
        print(f"\n{'=' * 50}")
        print(f"Running {name}")
        print(f"{'=' * 50}")
        if needs_args:
            result = test_suite(api_url, test_state)
        else:
            result = test_suite()
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
