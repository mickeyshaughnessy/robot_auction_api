#!/usr/bin/env python3

import redis, json, time, sys
from datetime import datetime

class RSXLogTailer:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
        self.last_seen = {}
        
    def format_log_entry(self, entry_str):
        try:
            entry = json.loads(entry_str)
            timestamp = datetime.fromtimestamp(entry['timestamp']).strftime('%H:%M:%S')
            method = entry.get('method', '?')
            path = entry.get('path', '?')
            status = entry.get('status', '?')
            ip = entry.get('ip', '?')
            username = entry.get('username', 'anon')
            user_agent = entry.get('user_agent', '')[:50]
            
            status_color = '\033[92m' if str(status).startswith('2') else '\033[91m' if str(status).startswith(('4', '5')) else '\033[93m'
            reset_color = '\033[0m'
            
            return f"{timestamp} {status_color}{status}{reset_color} {method:4} {path:30} {username:15} {ip:15} {user_agent}"
        except:
            return entry_str
    
    def tail_logs(self, follow=True):
        today = time.strftime('%Y-%m-%d')
        key = f"request_log:{today}"
        
        # Get existing logs first
        existing_logs = self.redis_client.lrange(key, 0, -1)
        if existing_logs:
            print(f"=== Showing last 20 entries from {today} ===")
            for entry in existing_logs[-20:]:
                print(self.format_log_entry(entry))
            self.last_seen[key] = len(existing_logs)
        
        if not follow:
            return
            
        print(f"\n=== Tailing live logs (Ctrl+C to stop) ===")
        try:
            while True:
                current_day = time.strftime('%Y-%m-%d')
                current_key = f"request_log:{current_day}"
                
                # Check if day changed
                if current_key != key:
                    print(f"\n=== Day changed to {current_day} ===")
                    key = current_key
                    self.last_seen[key] = 0
                
                current_length = self.redis_client.llen(key)
                last_seen = self.last_seen.get(key, 0)
                
                if current_length > last_seen:
                    new_entries = self.redis_client.lrange(key, last_seen, -1)
                    for entry in new_entries:
                        print(self.format_log_entry(entry))
                    self.last_seen[key] = current_length
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\nStopped tailing logs")
    
    def show_stats(self):
        today = time.strftime('%Y-%m-%d')
        key = f"request_log:{today}"
        
        entries = self.redis_client.lrange(key, 0, -1)
        if not entries:
            print("No log entries found for today")
            return
            
        stats = {'methods': {}, 'paths': {}, 'status_codes': {}, 'users': {}}
        
        for entry_str in entries:
            try:
                entry = json.loads(entry_str)
                method = entry.get('method', 'unknown')
                path = entry.get('path', 'unknown')
                status = str(entry.get('status', 'unknown'))
                user = entry.get('username', 'anonymous')
                
                stats['methods'][method] = stats['methods'].get(method, 0) + 1
                stats['paths'][path] = stats['paths'].get(path, 0) + 1
                stats['status_codes'][status] = stats['status_codes'].get(status, 0) + 1
                stats['users'][user] = stats['users'].get(user, 0) + 1
            except:
                continue
        
        print(f"=== Log stats for {today} ({len(entries)} total entries) ===")
        
        print("\nTop methods:")
        for method, count in sorted(stats['methods'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {method:6}: {count}")
            
        print("\nTop paths:")
        for path, count in sorted(stats['paths'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {path:30}: {count}")
            
        print("\nStatus codes:")
        for status, count in sorted(stats['status_codes'].items()):
            print(f"  {status:3}: {count}")
            
        print("\nTop users:")
        for user, count in sorted(stats['users'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {user:15}: {count}")

if __name__ == '__main__':
    tailer = RSXLogTailer()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'stats':
        tailer.show_stats()
    else:
        tailer.tail_logs()