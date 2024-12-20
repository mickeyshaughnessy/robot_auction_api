import time, sys
from test_utils import setup_redis, cleanup_redis
from auth_tests import run_auth_tests
from account_tests import run_account_tests
from buyer_tests import run_buyer_tests
from seller_tests import run_seller_tests
from shared_tests import run_shared_tests

def run_all_tests():
    start_time = time.time()
    print("\n🚀 Starting RSX API Test Suite")
    print("=" * 50)
    
    # Initialize Redis
    r = setup_redis()
    
    try:
        test_modules = [
            ("Authentication", run_auth_tests),
            ("Account Management", run_account_tests),
            ("Buyer Endpoints", run_buyer_tests),
            ("Seller Endpoints", run_seller_tests),
            ("Shared Endpoints", run_shared_tests)
        ]
        
        results = []
        for name, test_func in test_modules:
            print(f"\n▶️  Running {name} Tests...")
            try:
                test_func()
                results.append((name, True))
            except Exception as e:
                print(f"❌ Error in {name} tests: {str(e)}")
                results.append((name, False))
                if "--fail-fast" in sys.argv:
                    raise
    
    finally:
        cleanup_redis(r)
    
    # Print summary
    duration = time.time() - start_time
    print("\n📊 Test Suite Summary")
    print("=" * 50)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {name}")
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    print(f"\nPassed {passed}/{total} test modules")
    print(f"Duration: {duration:.2f} seconds")
    
    # Set exit code
    if passed != total:
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()