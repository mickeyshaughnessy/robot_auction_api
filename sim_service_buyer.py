import requests
import json
import time
import random

API_BASE_URL = "http://localhost:5001"  # Adjust this to the actual API server URL

class ServiceBuyer:
    def __init__(self, account_id, initial_balance):
        self.account_id = account_id
        self.balance = initial_balance

    def make_bid(self, service, lat, lon, price):
        url = f"{API_BASE_URL}/make_bid"
        data = {
            "account_id": self.account_id,
            "bid_price": price,
            "bid": {
                "service": service,
                "lat": lat,
                "lon": lon,
                "price": price,
                "bidder_account_id": self.account_id
            }
        }
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"Bid submitted successfully. Bid ID: {response.json()}")
            self.balance -= price
        elif response.status_code == 403:
            print("Insufficient funds to place bid.")
        else:
            print(f"Error submitting bid. Status code: {response.status_code}")

    def check_nearby_activity(self, lat, lon):
        url = f"{API_BASE_URL}/nearby"
        data = {"lat": lat, "lon": lon}
        response = requests.post(url, json=data)
        if response.status_code == 200:
            nearby_bids = response.json()
            print(f"Nearby activity: {len(nearby_bids)} bids found")
            for bid_id, bid_data in nearby_bids.items():
                print(f"Bid ID: {bid_id}, Data: {bid_data}")
        else:
            print(f"Error checking nearby activity. Status code: {response.status_code}")

def simulate_buyer_behavior(buyer, num_iterations):
    services = ["cleaning", "gardening", "painting", "plumbing"]
    for _ in range(num_iterations):
        action = random.choice(["bid", "check_nearby"])
        if action == "bid" and buyer.balance > 0:
            service = random.choice(services)
            lat = random.uniform(40.7, 40.8)
            lon = random.uniform(-74.1, -74.0)
            price = random.randint(10, min(100, buyer.balance))
            buyer.make_bid(service, lat, lon, price)
        elif action == "check_nearby":
            lat = random.uniform(40.7, 40.8)
            lon = random.uniform(-74.1, -74.0)
            buyer.check_nearby_activity(lat, lon)
        time.sleep(1)  # Wait for 1 second between actions

if __name__ == "__main__":
    buyer = ServiceBuyer("SIMULATED_BUYER_1", 1000)
    simulate_buyer_behavior(buyer, 10)
