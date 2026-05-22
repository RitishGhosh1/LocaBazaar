import json
import redis.asyncio as redis
from typing import Any, Optional

from app.core.config import config

class RedisManager:
    def __init__(self):
        # host='localhost' for now. When we Dockerize, we change this to 'redis'
        self.client = redis.Redis(
            host=config.REDIS_HOST, 
            port=config.REDIS_PORT, 
            decode_responses=True
        )

    async def set(self, key: str, value: Any, expire: int = 600):
        """Store data in Redis as a JSON string"""
        # We convert the Python dict/list to a JSON string
        await self.client.setex(key, expire, json.dumps(value))

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve data and convert back to Python object"""
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None

    async def delete(self, key: str):
        """Delete a specific key (Invalidation)"""
        await self.client.delete(key)

    async def delete_pattern(self, pattern: str):
        """Delete all keys matching a pattern (e.g., 'services:*')"""
        keys = await self.client.keys(pattern)
        if keys:
            await self.client.delete(*keys)

# Initialize a global instance
redis_cache = RedisManager()