#!/usr/bin/env python3
import redis
import config
import time

r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)
day = time.strftime('%Y-%m-%d')
log_key = f"request_log:{day}"

# Get logs
logs = []
while r.llen(log_key) > 0:
    log = r.lpop(log_key)
    if log:
        logs.append(log.decode())

# Write to file
if logs:
    with open(f"/var/log/rsx/api_{day}.log", "a") as f:
        for log in logs:
            f.write(log + "\n")