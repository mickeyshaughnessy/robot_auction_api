"""
Core utilities for the Robot Services Exchange API
"""

import math, redis, json, hashlib
from werkzeug.security import generate_password_hash, check_password_hash
import config

# Redis client setup
redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)

def calculate_distance(point1, point2):
    """Calculate great-circle distance between two points"""
    lat1, lon1, lat2, lon2 = *point1, *point2
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 3959 * 2 * math.asin(math.sqrt(a))  # Miles

def hash_password(password):
    """Create password hash"""
    return generate_password_hash(password)

def verify_password(stored_hash, provided_password):
    """Verify password against hash"""
    return check_password_hash(stored_hash, provided_password)

# Load seat data
seats = {}
try:
    with open('seats.dat', 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                seat_data = json.loads(line)
                seats[seat_data['id']] = seat_data
            except json.JSONDecodeError:
                print(f"Invalid seat data: {line}")
except Exception as e:
    print(f"Error loading seats: {str(e)}")
    # Add test seat for development
    seats['test_seat'] = {
        'id': 'test_seat',
        'owner': 'test_owner',
        'phrase': 'test_phrase'
    }
