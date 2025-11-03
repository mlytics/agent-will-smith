"""
Cache Service - Multi-tier caching with Redis and file fallback
"""

import os
import json
import logging
from typing import Optional, Any
import redis.asyncio as redis
import aiofiles
from pathlib import Path

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching API responses"""
    
    def __init__(self):
        self.redis_client = None
        self.redis_enabled = False
        self.cache_dir = Path(os.getenv("CACHE_DIR", "./cache"))
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize Redis if available
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_enabled = True
            logger.info("Redis cache enabled")
        except Exception as e:
            logger.warning(f"Redis not available, using file cache: {str(e)}")
            self.redis_enabled = False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        # Try Redis first
        if self.redis_enabled and self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get error: {str(e)}")
        
        # Fallback to file cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                async with aiofiles.open(cache_file, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            except Exception as e:
                logger.warning(f"File cache read error: {str(e)}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        json_value = json.dumps(value)
        
        # Try Redis first
        if self.redis_enabled and self.redis_client:
            try:
                await self.redis_client.setex(key, ttl, json_value)
                return True
            except Exception as e:
                logger.warning(f"Redis set error: {str(e)}")
        
        # Fallback to file cache (no TTL for files)
        cache_file = self.cache_dir / f"{key}.json"
        try:
            async with aiofiles.open(cache_file, 'w') as f:
                await f.write(json_value)
            return True
        except Exception as e:
            logger.error(f"File cache write error: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        success = True
        
        # Delete from Redis
        if self.redis_enabled and self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete error: {str(e)}")
                success = False
        
        # Delete from file cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"File cache delete error: {str(e)}")
                success = False
        
        return success
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

