import os
import redis
import json
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Подключение к Redis
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    decode_responses=True
)

def cache_user(user_email: str, user_data: dict, expire: int = 3600):
    """Кэширует данные пользователя на указанное время (по умолчанию 1 час)"""
    key = f"user:{user_email}"
    redis_client.setex(key, expire, json.dumps(user_data))

def get_cached_user(user_email: str) -> Optional[dict]:
    """Получает закэшированные данные пользователя"""
    key = f"user:{user_email}"
    data = redis_client.get(key)
    return json.loads(data) if data else None

def delete_cached_user(user_email: str):
    """Удаляет кэш пользователя"""
    key = f"user:{user_email}"
    redis_client.delete(key)

def test_redis_connection():
    """Проверяет подключение к Redis"""
    try:
        redis_client.ping()
        return True
    except Exception as e:
        print(f"Redis connection error: {e}")
        return False