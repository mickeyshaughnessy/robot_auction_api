import requests, random, time, uuid
import config

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
        # Register
        register_data = {
            'username': self.username,
            'password': self.password,
            'user_type': self.client_type
        }
        print(f"Attempting to register {self.username}")
        try:
            response = self.session.post(f"{self.api_url}/register", json=register_data)
            print(f"Registration response for {self.username}: {response.status_code}")
            print(f"Response content: {response.text}")
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Registration failed for {self.username}: {str(e)}")
            return False

        # Login
        login_data = {
            'username': self.username,
            'password': self.password
        }
        print(f"Attempting to login {self.username}")
        try:
            response = self.session.post(f"{self.api_url}/login", json=login_data)
            print(f"Login response for {self.username}: {response.status_code}")
            print(f"Response content: {response.text}")
            response.raise_for_status()
            self.token = response.json()['access_token']
            self.session.headers.update({'Authorization': f"Bearer {self.token}"})
            return True
        except requests.exceptions.RequestException as e:
            print(f"Login failed for {self.username}: {str(e)}")
            return False

    def simulate_action(self):
        if self.client_type == 'buyer':
            self.simulate_bid()
        elif self.client_type == 'seller':
            self.simulate_grab_job()

    def simulate_bid(self):
        bid_data = {
            'service': random.choice(['delivery', 'cleaning', 'security']),
            'lat': random.uniform(40.0, 41.0),
            'lon': random.uniform(-74.5, -73.5),
            'price': random.uniform(50, 200),
            'end_time': int(time.time()) + random.randint(3600, 86400)
        }
        print(f"Buyer {self.username} attempting to make a bid")
        try:
            response = self.session.post(f"{self.api_url}/make_bid", json={'bid': bid_data})
            print(f"Buyer {self.username} bid response: {response.status_code}")
            print(f"Response content: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Bid failed for {self.username}: {str(e)}")

    def simulate_grab_job(self):
        robot_data = {
            'services': random.choice([['delivery'], ['cleaning'], ['security'], ['delivery', 'cleaning']]),
            'lat': random.uniform(40.0, 41.0),
            'lon': random.uniform(-74.5, -73.5),
            'max_distance': random.uniform(5, 20)
        }
        print(f"Seller {self.username} attempting to grab a job")
        try:
            response = self.session.post(f"{self.api_url}/grab_job", json=robot_data)
            print(f"Seller {self.username} grab job response: {response.status_code}")
            print(f"Response content: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Grab job failed for {self.username}: {str(e)}")

def run_simulation(api_url, n_buyers, n_sellers, duration):
    clients = ([SimulatedClient(api_url, 'buyer') for _ in range(n_buyers)] + 
               [SimulatedClient(api_url, 'seller') for _ in range(n_sellers)])
    
    print("Starting client registration and login")
    for client in clients:
        if not client.register_and_login():
            print(f"Failed to set up client {client.username}. Skipping this client.")
            continue
        
        # Simulate a few actions for this client
        for _ in range(3):  # Perform 3 actions per client
            client.simulate_action()
            time.sleep(1)  # Wait 1 second between actions
    
    print("Simulation completed")

if __name__ == "__main__":
    N_BUYERS = 2
    N_SELLERS = 2

    print(f"Starting load test simulation with {N_BUYERS} buyers and {N_SELLERS} sellers")
    input("Press Enter to begin the simulation...")
    
    run_simulation(config.API_URL, N_BUYERS, N_SELLERS, 60)  # Run for 60 seconds
    
    input("Simulation finished. Press Enter to exit...")
