import requests, time, sys, statistics, os
from collections import deque

def load_test(requests_per_second):
   urls = {
       "target": "http://100.26.236.1:5001/ping",
       "google": "http://google.com"
   }
   latencies = {
       "target": deque(maxlen=100),
       "google": deque(maxlen=100)
   }
   
   while True:
       start_time = time.time()
       
       # Send N requests and collect latencies for each URL
       for _ in range(requests_per_second):
           for name, url in urls.items():
               try:
                   req_start = time.time()
                   requests.get(url)
                   latencies[name].append((time.time() - req_start) * 1000)
               except:
                   pass
       
       # Clear screen and print percentiles side by side
       os.system('cls' if os.name == 'nt' else 'clear')
       print(f"{'Target':^15} {'Google':^15}")
       print("-" * 30)
       
       if all(latencies.values()):  # If we have data for both
           sorted_latencies = {
               k: sorted(v) for k,v in latencies.items()
           }
           
           for i in range(0, 101, 5):
               percentiles = {}
               for name, sorted_lats in sorted_latencies.items():
                   idx = int((i / 100) * len(sorted_lats))
                   if idx >= len(sorted_lats): idx = -1
                   percentiles[name] = sorted_lats[idx]
               
               print(f"p{i:02d}: {percentiles['target']:6.1f}ms    {percentiles['google']:6.1f}ms")
               
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