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
        try:
            await self.client.setex(key, expire, json.dumps(value))
        except Exception as e:
            print(f"❌ Redis Cache Write Operational Failure: {str(e)}")

    async def get(self, key: str) -> Optional[Any]:
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"❌ Redis Cache Read Operational Failure: {str(e)}")
        return None

    async def clear(self, key: str):
        try:
            await self.client.delete(key)
        except Exception as e:
            print(f"❌ Redis Cache Key Eviction Operational Failure: {str(e)}")

    async def clear_pattern(self, pattern: str):
        try:
            # scan_iter streams matching keys without blocking Redis
            keys = [key async for key in self.client.scan_iter(match=pattern)]
            if keys:
                await self.client.delete(*keys)
        except Exception as e:
            print(f"❌ Redis Cache Pattern Eviction Operational Failure: {str(e)}")

# Initialize a single global instance mapping structure to handle shared system pools safely
redis_cache = RedisManager()