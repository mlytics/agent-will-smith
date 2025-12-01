"""
Search Service - Handles Google Custom Search and web scraping
"""

import os
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

from services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class SearchService:
    """Service for web search and content metadata extraction"""
    
    def __init__(self):
        self.gcs_api_key = os.getenv("GOOGLE_SEARCH_KEY")
        self.gcs_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.gemini_service = GeminiService()
        
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True
        )
    
    def _extract_domain(self, url: str) -> str:
        """
        Extract and normalize domain from URL
        e.g., "m.cnyes.com" -> "cnyes.com", "www.cnyes.com" -> "cnyes.com"
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Normalized domain string
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        
        # Remove mobile subdomain (m., mobile., etc.)
        if domain.startswith("m."):
            domain = domain[2:]
        elif domain.startswith("mobile."):
            domain = domain[7:]
        
        return domain
    
    async def get_metadata(
        self,
        url: str,
        query: Optional[str] = None,
        tag_prompt: Optional[str] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Extract metadata from URL
        
        Args:
            url: Target URL
            query: Optional search query
            tag_prompt: Optional tag generation prompt
            max_results: Maximum number of search results to return (default: 5)
            
        Returns:
            Dict with metadata (title, summary, sources, tags, images)
        """
        try:
            # Fetch and parse content
            content_data = await self._fetch_and_parse(url)
            
            # Extract and normalize domain
            domain = self._extract_domain(url)
            title = content_data.get("title", "")
            summary = content_data.get("summary", "")
            images = content_data.get("images", [])
            
            # Generate tags using Gemini if tag_prompt provided
            tags = []
            if tag_prompt and content_data.get("text"):
                tags = await self.gemini_service.generate_tags(
                    content=content_data["text"],
                    tag_prompt=tag_prompt
                )
            
            # Build sources list with domain filtering
            sources = []
            if query:
                # Add site: restriction to query (per spec: site:cnyes.com)
                site_query = f"site:{domain} {query}"
                search_results = await self._google_search(site_query, num_results=max_results)
                # Additional domain filtering as safety check
                filtered_results = []
                for r in search_results:
                    result_url = r.get("link", "")
                    if result_url:
                        result_domain = self._extract_domain(result_url)
                        if result_domain == domain:
                            filtered_results.append(r)
                
                sources = [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("link", ""),
                        "snippet": r.get("snippet", ""),
                        "score": 0.9 - (i * 0.1)  # Decreasing score
                    }
                    for i, r in enumerate(filtered_results[:max_results])
                ]
            
            return {
                "domain": domain,
                "title": title,
                "summary": summary,
                "sources": sources,
                "tags": tags,
                "images": images,
                "tokens_used": len(content_data.get("text", "").split()),  # Approximate
                "search_quota": 1 if query and sources else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting metadata: {str(e)}", exc_info=True)
            # Return minimal metadata
            domain = self._extract_domain(url) if url else ""
            return {
                "domain": domain,
                "title": "",
                "summary": "",
                "sources": [],
                "tags": [],
                "images": [],
                "tokens_used": 0,
                "search_quota": 0
            }
    
    async def _fetch_and_parse(self, url: str) -> Dict[str, Any]:
        """
        Fetch and parse URL content
        
        Args:
            url: URL to fetch
            
        Returns:
            Dict with title, summary, text, images
        """
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title = ""
            if soup.title:
                title = soup.title.string.strip()
            elif soup.find("meta", property="og:title"):
                title = soup.find("meta", property="og:title")["content"]
            
            # Extract description/summary
            summary = ""
            if soup.find("meta", property="og:description"):
                summary = soup.find("meta", property="og:description")["content"]
            elif soup.find("meta", attrs={"name": "description"}):
                summary = soup.find("meta", attrs={"name": "description"})["content"]
            
            # Extract text content (remove scripts, styles)
            for script in soup(["script", "style", "meta", "link"]):
                script.decompose()
            
            text = soup.get_text()
            text = ' '.join(text.split())  # Normalize whitespace
            text = text[:5000]  # Limit length
            
            # Extract images
            images = []
            seen_images = set()  # Track seen images to avoid duplicates
            
            # First, try Open Graph image (usually the best quality)
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                img_url = og_image["content"]
                if img_url not in seen_images:
                    seen_images.add(img_url)
                    # Convert relative URLs to absolute
                    if not img_url.startswith("http"):
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        elif img_url.startswith("/"):
                            img_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}{img_url}"
                        else:
                            img_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}/{img_url}"
                    images.append({
                        "url": img_url,
                        "width": 0,
                        "height": 0,
                        "type": "og:image"
                    })
            
            # Try Twitter card image
            twitter_image = soup.find("meta", attrs={"name": "twitter:image"})
            if twitter_image and twitter_image.get("content"):
                img_url = twitter_image["content"]
                if img_url not in seen_images:
                    seen_images.add(img_url)
                    if not img_url.startswith("http"):
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        elif img_url.startswith("/"):
                            img_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}{img_url}"
                    images.append({
                        "url": img_url,
                        "width": 0,
                        "height": 0,
                        "type": "twitter:image"
                    })
            
            # Extract images from <img> tags
            for img in soup.find_all("img", src=True):
                if len(images) >= 5:  # Limit to 5 images total
                    break
                    
                img_url = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                if not img_url:
                    continue
                
                # Convert relative URLs to absolute
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif img_url.startswith("/"):
                    img_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}{img_url}"
                elif not img_url.startswith("http"):
                    continue
                
                # Skip data URLs and very small images
                if img_url.startswith("data:") or "icon" in img_url.lower() or "logo" in img_url.lower():
                    continue
                
                if img_url not in seen_images:
                    seen_images.add(img_url)
                    images.append({
                        "url": img_url,
                        "width": int(img.get("width", 0)) if img.get("width") and str(img.get("width")).isdigit() else 0,
                        "height": int(img.get("height", 0)) if img.get("height") and str(img.get("height")).isdigit() else 0,
                        "type": "img_tag"
                    })
            
            return {
                "title": title,
                "summary": summary or text[:200],
                "text": text,
                "images": images
            }
            
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {str(e)}")
            return {
                "title": "",
                "summary": "",
                "text": "",
                "images": []
            }
    
    async def _google_search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform Google Custom Search
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search result dictionaries
        """
        if not self.gcs_api_key or not self.gcs_engine_id:
            logger.warning("Google Custom Search API key not configured")
            return []
        
        try:
            search_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.gcs_api_key,
                "cx": self.gcs_engine_id,
                "q": query,
                "num": min(num_results, 10)
            }
            
            response = await self.client.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("items", [])
            
            return [
                {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                }
                for item in results[:num_results]
            ]
            
        except Exception as e:
            logger.error(f"Error performing Google search: {str(e)}")
            return []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

