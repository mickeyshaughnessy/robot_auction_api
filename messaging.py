"""
Chat endpoints for the Robot Services Exchange API:
- /chat (POST) - Send message
- /chat (GET) - Get messages
"""

import json, time, uuid
from utils import redis_client, verify_password
import config

def send_chat(data):
    try:
        print(f"send_chat called with data: {json.dumps(data, indent=2)}")
        username = data.get('username')
        recipient = data.get('recipient')
        message = data.get('message')
        password = data.get('password')

        if not all([username, recipient, message, password]):
            return {"error": "Missing required parameters"}, 400
            
        if len(message) > 1000:
            return {"error": "Message exceeds 1000 characters"}, 400

        # Auth check
        user_data = redis_client.hget(config.REDHASH_ACCOUNTS, username)
        if not user_data:
            return {"error": "User not found"}, 404

        if isinstance(user_data, bytes):
            user_data = user_data.decode('utf-8')
        user_data = json.loads(user_data)
        
        if not verify_password(user_data.get('password', ''), password):
            return {"error": "Invalid password"}, 403

        # Verify recipient exists
        if not redis_client.hexists(config.REDHASH_ACCOUNTS, recipient):
            return {"error": "Recipient not found"}, 404

        msg_id = str(uuid.uuid4())
        msg_data = {
            'id': msg_id,
            'sender': username,
            'recipient': recipient,
            'message': message,
            'timestamp': int(time.time())
        }

        # Store in both chat histories
        redis_client.hset(f"chat:{recipient}", msg_id, json.dumps(msg_data))
        redis_client.hset(f"chat:{username}", msg_id, json.dumps(msg_data))

        return {"message_id": msg_id}, 200

    except Exception as e:
        print(f"Error in send_chat: {str(e)}")
        return {"error": "Internal server error"}, 500

def get_chat(data):
    try:
        print(f"get_chat called with data: {json.dumps(data, indent=2)}")
        username = data.get('username')
        password = data.get('password')

        if not all([username, password]):
            return {"error": "Missing required parameters"}, 400

        # Auth check
        user_data = redis_client.hget(config.REDHASH_ACCOUNTS, username)
        if not user_data:
            return {"error": "User not found"}, 404

        if isinstance(user_data, bytes):
            user_data = user_data.decode('utf-8')
        user_data = json.loads(user_data)
        
        if not verify_password(user_data.get('password', ''), password):
            return {"error": "Invalid password"}, 403

        # Get messages
        messages = []
        for _, msg_json in redis_client.hscan_iter(f"chat:{username}"):
            try:
                if isinstance(msg_json, bytes):
                    msg_json = msg_json.decode('utf-8')
                msg = json.loads(msg_json)
                messages.append(msg)
            except json.JSONDecodeError:
                print(f"Invalid message JSON: {msg_json}")

        messages.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return {"messages": messages}, 200

    except Exception as e:
        print(f"Error in get_chat: {str(e)}")
        return {"error": "Internal server error"}, 500