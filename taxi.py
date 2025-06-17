#!/usr/bin/env python3
import requests, json, time, random, hashlib, threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

API_URL = "https://rse-api.com:5002"
SEATS_FILE = "seats.dat"
AUSTIN_CENTER = (30.2672, -97.7431)

class RobotTaxi:
    def __init__(self, seat_data, robot_type="private"):
        self.seat_id = seat_data["id"]
        self.phrase = seat_data["phrase"] 
        self.owner = seat_data["owner"]
        self.type = robot_type
        self.lat, self.lon = self.generate_austin_location()
        self.capabilities = self.get_capabilities()
        self.max_distance = random.randint(5, 25)
        self.status = "IDLE"
        self.current_job = None
        self.jobs_completed = 0
        self.earnings = 0
        self.last_maintenance = time.time()
        
    def generate_austin_location(self):
        # Spread robots across Austin metro area
        lat_offset = random.uniform(-0.15, 0.15)  # ~10 mile radius
        lon_offset = random.uniform(-0.20, 0.20)
        return (AUSTIN_CENTER[0] + lat_offset, AUSTIN_CENTER[1] + lon_offset)
        
    def get_capabilities(self):
        if self.type == "tesla":
            return ["autonomous_taxi", "delivery", "courier", "airport_shuttle"]
        elif self.type == "corporate":
            return ["delivery", "courier", "transport", "cleaning"]
        else:
            # Private owners - more varied individual capabilities
            base_caps = ["taxi", "delivery"]
            optional_caps = ["courier", "cleaning", "security", "pet_sitting", "moving", "food_delivery"]
            
            # Random selection of 2-4 capabilities per private robot
            num_caps = random.randint(2, 4)
            selected = random.sample(optional_caps, min(num_caps-2, len(optional_caps)))
            return base_caps + selected
    
    def get_seat_credentials(self):
        secret = hashlib.md5(self.phrase.encode()).hexdigest()
        return {
            "id": self.seat_id,
            "owner": self.owner, 
            "secret": secret
        }
    
    def log_status(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        robot_id = self.seat_id[-4:]
        print(f"[{timestamp}] 🤖 {robot_id} ({self.type.upper()}) | {message}")
        
    def grab_job(self):
        if self.status != "IDLE":
            return
            
        try:
            payload = {
                "capabilities": ",".join(self.capabilities),
                "lat": self.lat,
                "lon": self.lon,
                "max_distance": self.max_distance,
                "seat": self.get_seat_credentials()
            }
            
            response = requests.post(f"{API_URL}/grab_job", json=payload, timeout=10)
            
            if response.status_code == 200:
                job = response.json()
                self.current_job = job
                self.status = "EN_ROUTE"
                self.log_status(f"🎯 JOB ACCEPTED: {job['service']} | ${job['price']:.2f} | {job['distance']:.1f}mi")
                return job
            elif response.status_code == 204:
                if random.random() < 0.1:  # Only log occasionally to avoid spam
                    self.log_status("⏳ No jobs available")
            elif response.status_code == 403:
                self.log_status("❌ Seat authentication failed")
            else:
                self.log_status(f"⚠️  API error: {response.status_code}")
                
        except requests.RequestException as e:
            self.log_status(f"🔌 Connection error: {str(e)[:50]}")
        
        return None
    
    def do_job(self):
        if not self.current_job or self.status != "EN_ROUTE":
            return
            
        job = self.current_job
        
        # Travel time based on distance
        travel_time = max(2, int(job.get('distance', 5) * 2))  # 2 min per mile
        self.status = "TRAVELING"
        self.log_status(f"🚗 Traveling to job location ({travel_time}min)")
        time.sleep(travel_time)
        
        # Job execution time
        service_time = random.randint(5, 20)
        self.status = "WORKING" 
        self.log_status(f"⚙️  Performing {job['service']} ({service_time}min)")
        time.sleep(service_time)
        
        # Complete job
        self.jobs_completed += 1
        self.earnings += job['price']
        self.status = "IDLE"
        self.log_status(f"✅ Job completed! Total: {self.jobs_completed} jobs | ${self.earnings:.2f} earned")
        
        # Move to new random location
        self.lat, self.lon = self.generate_austin_location()
        self.current_job = None
    
    def do_maintenance(self):
        if time.time() - self.last_maintenance > 3600:  # Every hour
            if random.random() < 0.1:  # 10% chance
                self.status = "MAINTENANCE"
                maintenance_time = random.randint(5, 15)
                self.log_status(f"🔧 Maintenance required ({maintenance_time}min)")
                time.sleep(maintenance_time)
                self.status = "IDLE"
                self.last_maintenance = time.time()
                self.log_status("🔧 Maintenance completed")

def load_seats(limit=110):
    seats = []
    try:
        with open(SEATS_FILE, 'r') as f:
            for i, line in enumerate(f):
                if i >= limit:
                    break
                seat_data = json.loads(line.strip().rstrip(','))
                seats.append(seat_data)
    except FileNotFoundError:
        print(f"❌ {SEATS_FILE} not found! Please ensure seats.dat exists.")
        exit(1)
    return seats

def create_fleet(seats):
    fleet = []
    tesla_fleet_size = len(seats) // 10  # 10% Tesla corporate
    corporate_fleet_size = len(seats) // 7  # ~14% Corporate 
    
    for i, seat in enumerate(seats):
        if i < tesla_fleet_size:
            robot_type = "tesla"
            # Override owner for Tesla fleet
            seat["owner"] = f"@tesla_fleet_{i:03d}"
        elif i < tesla_fleet_size + corporate_fleet_size:
            robot_type = "corporate" 
            seat["owner"] = f"@corp_logistics_{i:03d}"
        else:
            robot_type = "private"
            # Keep original owner from seats.dat
            
        robot = RobotTaxi(seat, robot_type)
        fleet.append(robot)
    
    return fleet

def robot_worker(robot):
    """Main loop for each robot"""
    while True:
        try:
            if robot.status == "IDLE":
                job = robot.grab_job()
                if job:
                    robot.do_job()
                else:
                    time.sleep(random.randint(10, 30))  # Wait before next attempt
            elif robot.status in ["EN_ROUTE", "TRAVELING", "WORKING"]:
                robot.do_job()
            else:
                time.sleep(5)
                
            # Random maintenance checks
            robot.do_maintenance()
            
        except KeyboardInterrupt:
            robot.log_status("🛑 Shutting down...")
            break
        except Exception as e:
            robot.log_status(f"💥 Error: {str(e)[:50]}")
            time.sleep(10)

def print_fleet_summary(fleet):
    print("\n" + "="*80)
    print("🤖 AUSTIN ROBOTAXI FLEET INITIALIZED")
    print("="*80)
    
    tesla_count = sum(1 for r in fleet if r.type == "tesla")
    corporate_count = sum(1 for r in fleet if r.type == "corporate") 
    private_count = sum(1 for r in fleet if r.type == "private")
    
    print(f"🚗 Tesla Fleet: {tesla_count} vehicles ({tesla_count/len(fleet)*100:.0f}%)")
    print(f"🏢 Corporate Fleet: {corporate_count} vehicles ({corporate_count/len(fleet)*100:.0f}%)")
    print(f"👤 Private Owners: {private_count} vehicles ({private_count/len(fleet)*100:.0f}%)")
    print(f"📍 Operating in Austin, TX metro area")
    print(f"🌐 API Endpoint: {API_URL}")
    print("="*80 + "\n")

if __name__ == "__main__":
    print("🚀 Loading Austin RoboTaxi Fleet Management System...")
    
    # Load seats and create fleet
    seats = load_seats(110)
    fleet = create_fleet(seats)
    print_fleet_summary(fleet)
    
    # Start all robots in parallel
    with ThreadPoolExecutor(max_workers=len(fleet)) as executor:
        try:
            print("▶️  Starting all robots...")
            futures = [executor.submit(robot_worker, robot) for robot in fleet]
            
            # Wait for all robots (runs indefinitely until Ctrl+C)
            for future in futures:
                future.result()
                
        except KeyboardInterrupt:
            print("\n🛑 Fleet shutdown initiated...")
            print("📊 Final fleet statistics:")
            
            total_jobs = sum(r.jobs_completed for r in fleet)
            total_earnings = sum(r.earnings for r in fleet)
            
            print(f"   Total jobs completed: {total_jobs}")
            print(f"   Total earnings: ${total_earnings:.2f}")
            print("👋 Goodbye!")