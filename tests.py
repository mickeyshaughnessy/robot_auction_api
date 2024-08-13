import unittest
import json
import redis
import uuid
from unittest.mock import patch, MagicMock
import handlers

class TestRobotMarketplace(unittest.TestCase):
    def setUp(self):
        self.redis = redis.StrictRedis()
        
        # Clean up any existing test data
        self.cleanup()
        
        # Set up test data
        self.setup_test_data()
        
    def tearDown(self):
        # Clean up test data after each test
        self.cleanup()
        
    def cleanup(self):
        for key in self.redis.scan_iter("REDHASH_TEST*"):
            self.redis.delete(key)
        
    def setup_test_data(self):
        # Set up test accounts
        test_accounts = {
            "REDHASH_TEST_ACCOUNT1": json.dumps({"balance": 1000}),
            "REDHASH_TEST_ACCOUNT2": json.dumps({"balance": 500}),
        }
        for key, value in test_accounts.items():
            self.redis.hset("REDHASH_TEST_ACCOUNTS", key, value)
        
        # Set up test bids
        test_bids = {
            str(uuid.uuid4()): json.dumps({
                "bidder_account_id": "REDHASH_TEST_ACCOUNT1",
                "service": "cleaning",
                "lat": 40.7128,
                "lon": -74.0060,
                "price": 50
            }),
            str(uuid.uuid4()): json.dumps({
                "bidder_account_id": "REDHASH_TEST_ACCOUNT2",
                "service": "gardening",
                "lat": 40.7129,
                "lon": -74.0061,
                "price": 75
            })
        }
        for key, value in test_bids.items():
            self.redis.hset("REDHASH_TEST_ALL_LIVE_BIDS", key, value)

    @patch('handlers.redis')
    def test_submit_bid_sufficient_funds(self, mock_redis):
        mock_redis.hget.return_value = json.dumps({"balance": 1000})
        mock_redis.hscan_iter.return_value = []
        mock_redis.hset.return_value = True

        bid_data = {
            "account_id": "REDHASH_TEST_ACCOUNT1",
            "bid_price": 100,
            "bid": {
                "service": "cleaning",
                "lat": 40.7128,
                "lon": -74.0060,
                "price": 100
            }
        }
        response, status = handlers.submit_bid(bid_data)
        self.assertEqual(status, 200)
        self.assertIsNotNone(response)
        print("PASS: Submit bid with sufficient funds test successful")

    @patch('handlers.redis')
    def test_submit_bid_insufficient_funds(self, mock_redis):
        mock_redis.hget.return_value = json.dumps({"balance": 500})
        mock_redis.hscan_iter.return_value = []

        bid_data = {
            "account_id": "REDHASH_TEST_ACCOUNT2",
            "bid_price": 1000,
            "bid": {
                "service": "gardening",
                "lat": 40.7129,
                "lon": -74.0061,
                "price": 1000
            }
        }
        response, status = handlers.submit_bid(bid_data)
        self.assertEqual(status, 403)
        self.assertEqual(response, "")
        print("PASS: Submit bid with insufficient funds test successful")

    @patch('handlers.redis')
    def test_nearby_activity(self, mock_redis):
        mock_bids = {
            "bid1": json.dumps({"service": "cleaning", "lat": 40.7128, "lon": -74.0060}),
            "bid2": json.dumps({"service": "gardening", "lat": 40.7129, "lon": -74.0061})
        }
        mock_redis.hgetall.return_value = mock_bids

        response, status = handlers.nearby_activity()
        self.assertEqual(status, 200)
        nearby_bids = json.loads(response)
        self.assertEqual(len(nearby_bids), 2)
        print("PASS: Nearby activity test successful")

    @patch('handlers.redis')
    def test_grab_job_match(self, mock_redis):
        mock_bids = {
            "bid1": json.dumps({
                "service": "cleaning",
                "lat": 40.7128,
                "lon": -74.0060,
                "price": 50
            })
        }
        mock_redis.hscan_iter.return_value = mock_bids.items()
        mock_redis.hset.return_value = True
        mock_redis.hdel.return_value = True

        robot_data = {
            "services": ["cleaning"],
            "lat": 40.7128,
            "lon": -74.0060,
            "max_distance": 1
        }
        response, status = handlers.grab_job(robot_data)
        self.assertEqual(status, 200)
        self.assertIsNotNone(response)
        self.assertEqual(response['status'], 'won')
        print("PASS: Grab job with matching criteria test successful")

    @patch('handlers.redis')
    def test_grab_job_no_match(self, mock_redis):
        mock_redis.hscan_iter.return_value = []

        robot_data = {
            "services": ["painting"],
            "lat": 41.8781,
            "lon": -87.6298,
            "max_distance": 0.1
        }
        response, status = handlers.grab_job(robot_data)
        self.assertEqual(status, 204)
        self.assertIsNone(response)
        print("PASS: Grab job with no matching criteria test successful")

    @patch('handlers.redis')
    def test_has_sufficient_funds(self, mock_redis):
        mock_redis.hget.return_value = json.dumps({"balance": 1000})
        mock_redis.hscan_iter.return_value = []

        data = {
            "account_id": "REDHASH_TEST_ACCOUNT1",
            "bid_price": 500
        }
        result = handlers.has_sufficient_funds(data)
        self.assertTrue(result)
        print("PASS: Has sufficient funds test successful")

    @patch('handlers.redis')
    def test_has_insufficient_funds(self, mock_redis):
        mock_redis.hget.return_value = json.dumps({"balance": 500})
        mock_redis.hscan_iter.return_value = []

        data = {
            "account_id": "REDHASH_TEST_ACCOUNT2",
            "bid_price": 1000
        }
        result = handlers.has_sufficient_funds(data)
        self.assertFalse(result)
        print("PASS: Has insufficient funds test successful")

if __name__ == '__main__':
    unittest.main(verbosity=2)
