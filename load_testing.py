import requests, random, time, uuid
import config

SERVICES = ['delivery', 'cleaning', 'security', 'gardening', 'pet_sitting', 'home_maintenance', 'tech_support', 'personal_shopping', 'event_planning', 'tutoring']

class SimulatedClient:
    def __init__(self, api_url, client_type):
        self.api_url = api_url
        self.client_type = client_type
        self.session = requests.Session()
        self.session.headers.update({'X-Simulation-Traffic': 'true'})
        self.username = f"sim_user_{uuid.uuid4().hex[:8]}"
        self.password = "password123"
        self.token = None

    def register_and_login(self):
        register_data = {'username': self.username, 'password': self.password, 'user_type': self.client_type}
        try:
            print(f"Registering {self.username}...")
            response = self.session.post(f"{self.api_url}/register", json=register_data, timeout=10)
            response.raise_for_status()
            print(f"Logging in {self.username}...")
            response = self.session.post(f"{self.api_url}/login", json=register_data, timeout=10)
            response.raise_for_status()
            self.token = response.json()['access_token']
            self.session.headers.update({'Authorization': f"Bearer {self.token}"})
            print(f"Setup completed for {self.username}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Setup failed for {self.username}: {str(e)}")
            return False

    def simulate_actions(self, num_actions=3):
        for i in range(num_actions):
            print(f"Simulating action {i+1} for {self.username}")
            if self.client_type == 'buyer':
                self.simulate_bid()
            elif self.client_type == 'seller':
                self.simulate_grab_job()

    def simulate_bid(self):
        bid_data = {
            'service': random.choice(SERVICES),
            'lat': random.uniform(40.0, 41.0),
            'lon': random.uniform(-74.5, -73.5),
            'price': random.uniform(50, 200),
            'end_time': int(time.time()) + random.randint(3600, 86400)
        }
        try:
            print(f"Buyer {self.username} submitting bid...")
            response = self.session.post(f"{self.api_url}/make_bid", json={'bid': bid_data}, timeout=10)
            print(f"Buyer {self.username} bid response: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Bid failed for {self.username}: {str(e)}")

    def simulate_grab_job(self):
        robot_data = {
            'services': random.sample(SERVICES, random.randint(1, 3)),
            'lat': random.uniform(40.0, 41.0),
            'lon': random.uniform(-74.5, -73.5),
            'max_distance': random.uniform(5, 20)
        }
        try:
            print(f"Seller {self.username} grabbing job...")
            response = self.session.post(f"{self.api_url}/grab_job", json=robot_data, timeout=10)
            print(f"Seller {self.username} grab job response: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Grab job failed for {self.username}: {str(e)}")

def run_simulation(api_url, n_buyers, n_sellers):
    clients = ([SimulatedClient(api_url, 'buyer') for _ in range(n_buyers)] + 
               [SimulatedClient(api_url, 'seller') for _ in range(n_sellers)])
    
    for i, client in enumerate(clients):
        print(f"Processing client {i+1}/{len(clients)}")
        if client.register_and_login():
            client.simulate_actions()
    
    print("Simulation completed")

if __name__ == "__main__":
    N_BUYERS, N_SELLERS = 10, 10
    print(f"Starting load test simulation with {N_BUYERS} buyers and {N_SELLERS} sellers")
    start_time = time.time()
    run_simulation(config.API_URL, N_BUYERS, N_SELLERS)
    end_time = time.time()
    print(f"Simulation completed in {end_time - start_time:.2f} seconds")