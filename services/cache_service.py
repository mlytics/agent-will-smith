"""
Cache Service - File-based caching
"""

import os
import json
import logging
from typing import Optional, Any
import aiofiles
from pathlib import Path

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching API responses using file system"""
    
    def __init__(self):
        self.cache_dir = Path(os.getenv("CACHE_DIR", "./cache"))
        self.cache_dir.mkdir(exist_ok=True)
        logger.info("File cache initialized")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
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
            ttl: Time to live in seconds (not used for file cache, kept for API compatibility)
            
        Returns:
            True if successful
        """
        json_value = json.dumps(value)
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
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                cache_file.unlink()
                return True
            except Exception as e:
                logger.warning(f"File cache delete error: {str(e)}")
                return False
        return True
    
    async def close(self):
        """Close cache service (no-op for file cache)"""
        pass
