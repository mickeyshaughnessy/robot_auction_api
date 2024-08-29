import requests, random, time, uuid, json
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "http://127.0.0.1:5001"
SERVICES = ["delivery", "cleaning", "security", "lawn_mowing", "pet_care"]

def create_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    return session

def register_user(session, username, password):
    try:
        response = session.post(f"{API_URL}/register", json={"username": username, "password": password})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error registering user {username}: {e}")
        return None

def login_user(session, username, password):
    try:
        response = session.post(f"{API_URL}/login", json={"username": username, "password": password})
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error logging in user {username}: {e}")
        return None

def simulate_buyer(session, token):
    headers = {"Authorization": f"Bearer {token}"}
    bid = {
        "service": random.choice(SERVICES),
        "lat": random.uniform(40.0, 41.0),
        "lon": random.uniform(-74.5, -73.5),
        "price": random.uniform(50, 200),
        "end_time": int(time.time()) + random.randint(3600, 86400),
        "simulated": True 
    }
    try:
        response = session.post(f"{API_URL}/make_bid", json=bid, headers=headers)
        response.raise_for_status()
        print(f"Buyer bid: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error submitting bid: {e}")
        print(f"Request data: {json.dumps(bid, indent=2)}")
        if hasattr(e.response, 'text'):
            print(f"Response content: {e.response.text}")

def simulate_seller(session, token):
    headers = {"Authorization": f"Bearer {token}"}
    job_request = {
        "service": ",".join(random.sample(SERVICES, random.randint(1, 3))),
        "lat": random.uniform(40.0, 41.0),
        "lon": random.uniform(-74.5, -73.5),
        "max_distance": random.uniform(1, 10)
    }
    try:
        response = session.post(f"{API_URL}/grab_job", json=job_request, headers=headers)
        response.raise_for_status()
        print(f"Seller job grab: {response.status_code}")
        print(f"Response content: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error grabbing job: {e}")
        print(f"Request data: {json.dumps(job_request, indent=2)}")
        if hasattr(e.response, 'text'):
            print(f"Response content: {e.response.text}")

def run_simulation(num_users=10, duration=300):
    session = create_session()
    users = [f"user_{uuid.uuid4().hex[:8]}" for _ in range(num_users)]
    tokens = []
    for user in users:
        if register_user(session, user, "password123"):
            token = login_user(session, user, "password123")
            if token:
                tokens.append(token)
    
    if not tokens:
        print("Failed to register and login users. Exiting simulation.")
        return

    start_time = time.time()
    with ThreadPoolExecutor(max_workers=20) as executor:
        while time.time() - start_time < duration:
            executor.submit(simulate_buyer, session, random.choice(tokens))
            executor.submit(simulate_seller, session, random.choice(tokens))
            time.sleep(random.uniform(0.5, 1.0))

if __name__ == "__main__":
    run_simulation()