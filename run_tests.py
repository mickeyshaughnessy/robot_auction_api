import time, sys
from test_utils import setup_redis, cleanup_redis
from auth_tests import test_auth
from account_tests import test_account
from buyer_tests import test_buyer
from seller_tests import test_seller
from shared_tests import test_shared

def run_all_tests():
    start_time = time.time()
    print("\n🚀 Starting RSX API Test Suite")
    print("=" * 50)
    
    r = setup_redis()
    results = []
    fail_fast = "--fail-fast" in sys.argv

    # Note: Each test_func should return True if all tests pass, False otherwise.
    test_modules = [
        ("Authentication", test_auth),
        ("Account Management", test_account),
        ("Buyer Endpoints", test_buyer),
        ("Seller Endpoints", test_seller),
        ("Shared Endpoints", test_shared)
    ]

    try:
        for name, test_func in test_modules:
            print(f"\n▶️  Running {name} Tests...")
            try:
                passed = test_func()
                if not passed:
                    print(f"❌ {name} module reported failures internally.")
                    results.append((name, False))
                    if fail_fast:
                        sys.exit(1)
                else:
                    results.append((name, True))
            except Exception as e:
                print(f"❌ Error in {name} tests: {str(e)}")
                results.append((name, False))
                if fail_fast:
                    sys.exit(1)
    finally:
        cleanup_redis(r)
    
    duration = time.time() - start_time
    print("\n📊 Test Suite Summary")
    print("=" * 50)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {name}")
    
    passed_count = sum(1 for _, p in results if p)
    total = len(results)
    print(f"\nPassed {passed_count}/{total} test modules")
    print(f"Duration: {duration:.2f} seconds")
    
    if passed_count != total:
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
