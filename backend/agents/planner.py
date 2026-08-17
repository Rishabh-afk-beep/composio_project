"""
Research Planner – generates targeted search queries for an app.
"""
from typing import List


def generate_search_queries(app_name: str, website: str) -> List[str]:
    """Return 2-3 focused search queries for Firecrawl."""
    queries = [
        f"{app_name} developer API documentation REST GraphQL",
        f"{app_name} authentication OAuth API key developer access",
    ]
    # MCP-specific query
    queries.append(f"{app_name} MCP model context protocol server")
    return queries


def generate_scrape_targets(app_name: str, website: str) -> List[str]:
    """Return likely official doc URLs to try scraping directly."""
    domain = website.rstrip("/")
    if not domain.startswith("http"):
        domain = f"https://{domain}"
    targets = []
    # Common developer doc paths
    for path in ["/developers", "/developer", "/docs/api", "/api", "/docs"]:
        targets.append(f"{domain}{path}")
    return targets[:2]  # limit to 2
