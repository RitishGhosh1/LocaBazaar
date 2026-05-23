import json
import redis.asyncio as redis
from typing import Any, Optional

from app.core.config import config

class RedisManager:
    def __init__(self):
        # 🎯 THE FIX: Initialize the connection string dynamically from your Pydantic layer
        print(f"📡 Initializing asynchronous Redis cache client framework via network token configuration...")
        self.client = redis.Redis.from_url(
            config.REDIS_URL,
            decode_responses=True,
            socket_timeout=5.0  # Defensive timeout guard preventing worker deadlocks during deployment lag
        )

    async def set(self, key: str, value: Any, expire: int = 600):
        """Store data in Redis as a JSON string"""
        try:
            await self.client.setex(key, expire, json.dumps(value))
        except Exception as e:
            print(f"❌ Redis Cache Write Operational Failure: {str(e)}")

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve data and convert back to Python object"""
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"❌ Redis Cache Read Operational Failure: {str(e)}")
        return None

    async def delete(self, key: str):
        """Delete a specific key (Invalidation)"""
        try:
            await self.client.delete(key)
        except Exception as e:
            print(f"❌ Redis Cache Key Eviction Operational Failure: {str(e)}")

    async def delete_pattern(self, pattern: str):
        """Delete all keys matching a pattern (e.g., 'services:*')"""
        try:
            keys = await self.client.keys(pattern)
            if keys:
                await self.client.delete(*keys)
        except Exception as e:
            print(f"❌ Redis Cache Pattern Eviction Operational Failure: {str(e)}")

# Initialize a single global instance mapping structure to handle shared system pools safely
redis_cache = RedisManager()