"""
Content Service - Handles content fetching and storage
"""

import os
import logging
from typing import Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ContentService:
    """Service for fetching and managing content"""
    
    def __init__(self, cache_service=None):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        
        # In-memory content storage (fast access)
        self.content_store: Dict[str, str] = {}
        
        # Cache service for persistent storage
        self.cache_service = cache_service
    
    async def fetch_content(self, url: str) -> str:
        """
        Fetch content from URL
        
        Args:
            url: URL to fetch
            
        Returns:
            Content text
        """
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove scripts, styles, etc.
            for script in soup(["script", "style", "meta", "link", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract main content
            # Try common content selectors
            content_selectors = [
                "article",
                "main",
                ".content",
                "#content",
                ".post-content",
                ".entry-content"
            ]
            
            content_text = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content_text = ' '.join([elem.get_text() for elem in elements])
                    break
            
            # Fallback to body text
            if not content_text:
                content_text = soup.get_text()
            
            # Normalize whitespace
            content_text = ' '.join(content_text.split())
            
            # Limit length
            return content_text[:20000]
            
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {str(e)}")
            return ""
    
    async def get_content(self, content_id: str) -> str:
        """
        Get content by ID
        
        Args:
            content_id: Content identifier
            
        Returns:
            Content text
        """
        # Check in-memory store first (fastest)
        if content_id in self.content_store:
            return self.content_store[content_id]
        
        # Check persistent cache if available
        if self.cache_service:
            cache_key = f"content_{content_id}"
            cached_data = await self.cache_service.get(cache_key)
            if cached_data:
                # Restore to in-memory store for faster future access
                content_text = cached_data.get("content", "")
                if content_text:
                    self.content_store[content_id] = content_text
                    logger.info(f"Content ID {content_id} restored from cache")
                    return content_text
        
        # Not found in memory or cache
        logger.warning(f"Content ID {content_id} not found")
        return ""
    
    async def save_content(self, content_id: str, content: str, url: Optional[str] = None):
        """
        Save content with ID
        
        Args:
            content_id: Content identifier
            content: Content text
            url: Optional source URL
        """
        # Save to in-memory store (fast access)
        self.content_store[content_id] = content
        
        # Save to persistent cache for durability across restarts
        if self.cache_service:
            cache_key = f"content_{content_id}"
            cache_data = {
                "content": content,
                "url": url,
                "content_id": content_id
            }
            # Use maximum TTL (50 years) to persist content indefinitely
            max_ttl = 1_577_836_800  # 50 years in seconds
            await self.cache_service.set(cache_key, cache_data, ttl=max_ttl)
            logger.debug(f"Content ID {content_id} saved to persistent cache")
    
    async def reserve_content_id_from_url(self, url: str) -> str:
        """
        Generate or retrieve content ID for URL
        
        Args:
            url: Source URL
            
        Returns:
            Content ID
        """
        import hashlib
        return hashlib.sha256(url.encode()).hexdigest()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

