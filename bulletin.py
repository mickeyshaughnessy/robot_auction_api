"""
Bulletin board endpoints for the Robot Services Exchange API:
- /bulletin (POST) - Post bulletin
- /bulletin (GET) - Get bulletins
"""

import json, time, uuid
from utils import redis_client, verify_password
import config

def post_bulletin(data):
    try:
        print(f"post_bulletin called with data: {json.dumps(data, indent=2)}")
        username = data.get('username')
        password = data.get('password')
        title = data.get('title')
        content = data.get('content')
        category = data.get('category', 'general')

        if not all([username, password, title, content]):
            return {"error": "Missing required parameters"}, 400
            
        if len(title) > 100:
            return {"error": "Title exceeds 100 characters"}, 400
            
        if len(content) > 2000:
            return {"error": "Content exceeds 2000 characters"}, 400

        # Auth check
        user_data = redis_client.hget(config.REDHASH_ACCOUNTS, username)
        if not user_data:
            return {"error": "User not found"}, 404

        if isinstance(user_data, bytes):
            user_data = user_data.decode('utf-8')
        user_data = json.loads(user_data)
        
        if not verify_password(user_data.get('password', ''), password):
            return {"error": "Invalid password"}, 403

        bulletin_id = str(uuid.uuid4())
        bulletin_data = {
            'id': bulletin_id,
            'title': title,
            'content': content,
            'category': category,
            'author': username,
            'timestamp': int(time.time())
        }

        redis_client.hset('bulletins', bulletin_id, json.dumps(bulletin_data))
        return {"bulletin_id": bulletin_id}, 200

    except Exception as e:
        print(f"Error in post_bulletin: {str(e)}")
        return {"error": "Internal server error"}, 500

def get_bulletins(data):
    try:
        print(f"get_bulletins called with data: {json.dumps(data, indent=2)}")
        category = data.get('category')
        limit = min(int(data.get('limit', 20)), 100)  # Cap at 100

        bulletins = []
        for _, bulletin_json in redis_client.hscan_iter('bulletins'):
            try:
                if isinstance(bulletin_json, bytes):
                    bulletin_json = bulletin_json.decode('utf-8')
                bulletin = json.loads(bulletin_json)
                if category and bulletin.get('category') != category:
                    continue
                bulletins.append(bulletin)
            except json.JSONDecodeError:
                print(f"Invalid bulletin JSON: {bulletin_json}")

        bulletins.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return {"bulletins": bulletins[:limit]}, 200

    except Exception as e:
        print(f"Error in get_bulletins: {str(e)}")
        return {"error": "Internal server error"}, 500