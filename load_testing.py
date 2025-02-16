import requests, time, sys, statistics, os
from collections import deque

def load_test(requests_per_second):
    url = "http://100.26.236.1:5001/ping"
    latencies = deque(maxlen=100)  # Rolling window of last 100 latencies
    
    while True:
        start_time = time.time()
        
        # Send N requests and collect latencies
        for _ in range(requests_per_second):
            try:
                req_start = time.time()
                requests.get(url)
                latencies.append((time.time() - req_start) * 1000)  # Convert to ms
            except:
                pass
        
        # Clear screen and print percentiles
        os.system('cls' if os.name == 'nt' else 'clear')
        if latencies:
            sorted_latencies = sorted(latencies)
            for i in range(0, 101, 5):  # 0, 5, 10, ..., 95, 100
                idx = int((i / 100) * len(sorted_latencies))
                if idx >= len(sorted_latencies): idx = -1
                print(f"p{i:02d}: {sorted_latencies[idx]:.1f}ms")
                
        # Wait until next second
        time_to_sleep = 1 - (time.time() - start_time)
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <requests_per_second>")
        sys.exit(1)
    try:
        load_test(int(sys.argv[1]))
    except KeyboardInterrupt:
        print("\nStopped")
