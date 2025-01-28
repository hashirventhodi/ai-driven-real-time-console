# conversation/conversation_manager.py
from typing import List
from server.utils.redis_client import redis_client

def add_message_to_history(user_id: str, message: str):
    key = f"conversation:{user_id}"
    redis_client.rpush(key, message)

def get_conversation_history(user_id: str, limit: int = 10) -> List[str]:
    key = f"conversation:{user_id}"
    length = redis_client.llen(key)
    start = max(length - limit, 0)
    end = length - 1
    return redis_client.lrange(key, start, end)

def clear_conversation_history(user_id: str):
    key = f"conversation:{user_id}"
    redis_client.delete(key)
