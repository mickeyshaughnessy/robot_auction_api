import redis

# Connect to Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Get all keys
all_keys = redis_client.keys('*')

# Filter and delete keys that don't start with 'REDHASH'
keys_to_delete = [key for key in all_keys if not key.startswith(b'REDHASH')]

if keys_to_delete:
    redis_client.delete(*keys_to_delete)
    print(f"Deleted {len(keys_to_delete)} keys")
else:
    print("No keys to delete")
