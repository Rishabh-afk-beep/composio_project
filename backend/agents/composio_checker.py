"""
Composio toolkit-catalog checker.
GET /api/v3.1/toolkits — searches by name and checks for exact / alias matches.
"""
import httpx
from typing import Optional, List
from backend.config import COMPOSIO_API_KEY
from backend.research.cache import get_cache, set_cache

_BASE = "https://backend.composio.dev/api/v3.1"
_TIMEOUT = 15.0

# Aliases map: canonical name (lowercase) → list of search terms to try
ALIASES: dict = {
    "salesforce commerce cloud": ["sfcc", "salesforce commerce cloud"],
    "magento": ["magento", "adobe commerce"],
    "lark": ["lark", "larksuite"],
    "zoho crm": ["zoho crm", "zoho"],
    "meta ads": ["meta ads", "facebook", "facebook marketing"],
    "whatsapp business": ["whatsapp", "whatsapp business"],
    "threads": ["threads", "meta threads"],
    "amazon selling partner api": ["amazon", "amazon sp-api", "amazon seller"],
    "mongodb atlas": ["mongodb", "mongodb atlas"],
    "jira": ["jira", "atlassian jira", "jira software"],
    "quickbooks": ["quickbooks", "quickbooks online"],
    "google ads": ["google ads", "googleads"],
    "linkedin ads": ["linkedin ads", "linkedin"],
    "zoho cliq": ["zoho cliq", "zoho"],
    "mermaid cli": ["mermaid"],
    "youtube transcript": ["youtube"],
    "notebooklm": ["notebooklm", "notebook lm"],
    "otter ai": ["otter", "otter ai"],
}


def _normalize(name: str) -> str:
    return name.lower().replace(" ", "").replace("-", "").replace("_", "")


from tenacity import retry, stop_after_attempt, wait_exponential_jitter

@retry(wait=wait_exponential_jitter(initial=2, max=15), stop=stop_after_attempt(3), reraise=True)
async def _fetch_toolkits(query: str) -> List[dict]:
    cache_key = f"composio_search:{query}"
    cached = get_cache(cache_key)
    if cached is not None:
        return cached

    headers = {}
    if COMPOSIO_API_KEY:
        headers["x-api-key"] = COMPOSIO_API_KEY

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.get(
            f"{_BASE}/toolkits",
            headers=headers,
            params={"query": query, "limit": 20},
        )
        if r.status_code == 200:
            items = r.json().get("items", [])
            set_cache(cache_key, items)
            return items
        else:
            print(f"[Composio] API returned {r.status_code} for query '{query}'")
            raise Exception(f"Composio API error {r.status_code}")


async def check_composio_coverage(app_name: str) -> dict:
    """
    Returns a dict matching ComposioStatus schema fields.
    Searches the live Composio toolkit catalog with aliases.
    """
    name_lower = app_name.lower()
    search_terms: List[str] = ALIASES.get(name_lower, [app_name])

    for term in search_terms:
        try:
            items = await _fetch_toolkits(term)
        except Exception as e:
            print(f"[Composio] Request completely failed for term '{term}': {e}")
            return {
                "currently_supported": "unknown",
                "toolkit_slug": None,
                "toolkit_source_url": None,
            }
        norm_app = _normalize(app_name)

        for item in items:
            norm_name = _normalize(item.get("name", ""))
            norm_slug = _normalize(item.get("slug", ""))
            # Exact or substring match
            if norm_app == norm_name or norm_app == norm_slug:
                return {
                    "currently_supported": "yes",
                    "toolkit_slug": item.get("slug"),
                    "toolkit_source_url": f"https://composio.dev/toolkits/{item.get('slug')}",
                }
            # Alias substring match (e.g. "mongodb" inside "mongodbatlas")
            for alias_term in search_terms:
                if _normalize(alias_term) in norm_slug or _normalize(alias_term) in norm_name:
                    # flag as fuzzy – don't mark as definitive yes
                    return {
                        "currently_supported": "fuzzy_match",
                        "toolkit_slug": item.get("slug"),
                        "toolkit_source_url": f"https://composio.dev/toolkits/{item.get('slug')}",
                    }

    return {
        "currently_supported": "no",
        "toolkit_slug": None,
        "toolkit_source_url": None,
    }
