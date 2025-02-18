"""
Authentication endpoints for the Robot Services Exchange API:
- /register - Create new account
- /login - Authenticate and get token
"""

import json, secrets
from utils import redis_client, hash_password, verify_password
import config


def register(data):
    try:
        print(f"register called with data: {json.dumps(data, indent=2)}")
        username, password = data.get('username'), data.get('password')
        
        if not all([username, password]):
            return {"error": "Missing required parameters"}, 400
            
        if len(username) < 3 or len(username) > 20:
            return {"error": "Username must be between 3 and 20 characters"}, 400
            
        if len(password) < 8:
            return {"error": "Password must be at least 8 characters"}, 400

        if redis_client.hexists(config.REDHASH_ACCOUNTS, username):
            return {"error": "Username already exists"}, 409

        account_data = {
            'username': username,
            'password': hash_password(password),
            'stars': 0,
            'total_ratings': 0
        }

        redis_client.hset(config.REDHASH_ACCOUNTS, username, json.dumps(account_data))
        return {"message": "Registration successful"}, 201

    except Exception as e:
        print(f"Error in register: {str(e)}")
        return {"error": "Internal server error"}, 500
def login(data):
    try:
        print(f"login called with data: {json.dumps(data, indent=2)}")
        username, password = data.get('username'), data.get('password')
        
        if not all([username, password]):
            return {"error": "Missing required parameters"}, 400
            
        user_data = redis_client.hget(config.REDHASH_ACCOUNTS, username)
        if not user_data:
            return {"error": "User not found"}, 404
            
        if isinstance(user_data, bytes):
            user_data = user_data.decode('utf-8')
        user_data = json.loads(user_data)
        
        if not verify_password(user_data.get('password', ''), password):
            return {"error": "Invalid password"}, 403

        # Generate and store token
        token = f"token_{username}_{secrets.token_hex(16)}"
        redis_client.setex(
            f"auth_token:{token}",
            24 * 60 * 60,  # 24 hour expiry
            username
        )
            
        return {
            "access_token": token,
            "token_type": "bearer"
        }, 200
            
    except Exception as e:
        print(f"Error in login: {str(e)}")
        return {"error": "Internal server error"}, 500
