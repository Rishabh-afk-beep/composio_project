"""
Firecrawl client – search + scrape with SQLite caching and exponential backoff.
"""
import asyncio
import time
import httpx
from typing import List, Dict, Any

from backend.config import FIRECRAWL_API_KEY
from backend.research.cache import get_cache, set_cache

_BASE = "https://api.firecrawl.dev/v1"
_TIMEOUT = 30.0
_MAX_RETRIES = 3
_BACKOFF_BASE = 2


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if FIRECRAWL_API_KEY:
        h["Authorization"] = f"Bearer {FIRECRAWL_API_KEY}"
    return h


async def _post_with_retry(url: str, payload: dict) -> dict:
    delay = 1
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                r = await client.post(url, headers=_headers(), json=payload)
                if r.status_code == 429:
                    wait = delay * (_BACKOFF_BASE ** attempt)
                    print(f"[Firecrawl] Rate-limited. Waiting {wait}s …")
                    await asyncio.sleep(wait)
                    continue
                r.raise_for_status()
                return r.json()
        except httpx.TimeoutException:
            print(f"[Firecrawl] Timeout on attempt {attempt}")
        except Exception as e:
            print(f"[Firecrawl] Error on attempt {attempt}: {e}")
        if attempt < _MAX_RETRIES:
            await asyncio.sleep(delay * attempt)
    return {}


async def firecrawl_search(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Return list of {url, title, markdown} items."""
    cache_key = f"fc_search:{query}"
    cached = get_cache(cache_key)
    if cached is not None:
        return cached

    if not FIRECRAWL_API_KEY:
        print(f"[Firecrawl] No API key – skipping search for: {query}")
        return []

    payload = {"query": query, "limit": limit}
    data = await _post_with_retry(f"{_BASE}/search", payload)

    items = []
    for item in data.get("data", []):
        items.append({
            "url": item.get("url", ""),
            "title": item.get("title", ""),
            "markdown": (item.get("markdown") or item.get("description") or "")[:2000],
        })

    set_cache(cache_key, items)
    return items


async def firecrawl_scrape(url: str) -> str:
    """Return markdown content of a scraped page."""
    cache_key = f"fc_scrape:{url}"
    cached = get_cache(cache_key)
    if cached is not None:
        return cached

    if not FIRECRAWL_API_KEY:
        return ""

    payload = {"url": url, "formats": ["markdown"]}
    data = await _post_with_retry(f"{_BASE}/scrape", payload)
    content = (data.get("data") or {}).get("markdown", "")[:3000]
    set_cache(cache_key, content)
    return content
