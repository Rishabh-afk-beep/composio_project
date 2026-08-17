"""
Research workflow – orchestrates the full pipeline for a single app.

Architecture:
  Planner -> Firecrawl search -> LLM extraction (API, Auth, MCP/Webhooks/Docs)
  -> Composio coverage check -> Verification -> Deterministic scoring -> Analyst reason

Uses simple async orchestration rather than LangGraph fan-out to keep it
debuggable and interview-explainable.
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from urllib.parse import urlparse

from backend.schemas import (
    AppResearch, API, Authentication, Webhooks, MCP,
    Documentation, ComposioStatus, Recommendation, Verification, Evidence,
)
from backend.agents.planner import generate_search_queries
from backend.agents.api_researcher import research_api
from backend.agents.auth_researcher import research_auth
from backend.agents.mcp_researcher import research_mcp_webhooks_docs
from backend.agents.composio_checker import check_composio_coverage
from backend.agents.verifier import verify_research
from backend.agents.analyst import generate_analyst_reason
from backend.research.firecrawl_client import firecrawl_search, firecrawl_scrape
from backend.scoring.scorer import calculate_score, determine_buildability, determine_priority, generate_recommendation


def _build_context(search_results: List[Dict[str, Any]], scraped_contents: Dict[str, str]) -> str:
    """Flatten search results and scraped content into a single context string for LLM prompts."""
    parts = []
    for item in search_results:
        url = item.get("url", "")
        title = item.get("title", "")
        # Use deep scraped content if available, fallback to short markdown snippet
        scraped_text = scraped_contents.get(url, "")
        if scraped_text:
            md = scraped_text[:5000]  # Give it more room if we deeply scraped
        else:
            md = item.get("markdown", "")[:1500]
        parts.append(f"SOURCE: {title}\nURL: {url}\n{md}\n---")
    return "\n".join(parts)


def _extract_evidence(search_results: List[Dict[str, Any]], app_name: str, website: str = "") -> List[Evidence]:
    """Create Evidence objects from search results (raw sources)."""
    evidences = []
    now = datetime.now(timezone.utc)
    for item in search_results:
        url = item.get("url", "")
        title = item.get("title", "")
        md = item.get("markdown", "")[:200]

        # Classify source type
        source_type = "search_result"
        url_lower = url.lower()
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
            
        if "reddit.com" in domain or "stackoverflow.com" in domain or "community." in domain:
            source_type = "community"
        elif "github.com" in domain:
            source_type = "official_github"
        elif "blog." in domain:
            source_type = "official_blog"
        elif domain in ["medium.com", "dev.to", "youtube.com", "getpassionfruit.com"]:
            source_type = "third_party"
        elif "developer" in domain or "/api" in url_lower or "/docs" in url_lower:
            source_type = "official_docs"
        elif website and (domain == website or domain.endswith("." + website)):
            source_type = "official_site"

        evidences.append(Evidence(
            field="general",
            claim=f"Source found for {app_name}",
            source_url=url,
            source_title=title,
            source_type=source_type,
            evidence_excerpt=md,
            checked_at=now,
        ))
    return evidences


def _infer_website(search_results: List[Dict[str, Any]], app_name: str) -> str:
    """Try to infer the official website from search results."""
    app_lower = app_name.lower().replace(" ", "")
    candidates = {}
    for item in search_results:
        url = item.get("url", "")
        if not url:
            continue
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        # Skip generic domains
        skip_domains = {"youtube.com", "github.com", "reddit.com", "stackoverflow.com",
                        "medium.com", "dev.to", "npmjs.com", "pypi.org", "mcpservers.org",
                        "apollographql.com", "gitguardian.com"}
        if domain in skip_domains:
            continue
        # Prefer domains that contain the app name
        if app_lower in domain.replace(".", "").replace("-", ""):
            candidates[domain] = candidates.get(domain, 0) + 10
        else:
            candidates[domain] = candidates.get(domain, 0) + 1

    if candidates:
        best = max(candidates, key=candidates.get)
        return best
    return "unknown.com"


async def run_research_pipeline(app_name: str, category: str, website: str) -> AppResearch:
    """Execute the full research pipeline for a single app."""

    # ── Step 1: Plan ──
    print(f"\n{'='*60}")
    print(f"  [1/6] Planning research for {app_name}...")
    queries = generate_search_queries(app_name, website)
    print(f"  [PLANNER] queries = {queries}")

    # ── Step 2: Firecrawl search ──
    print(f"  [2/6] Searching web via Firecrawl...")
    all_results = []
    seen_urls = set()
    unique_results = []

    for q in queries:  # process ALL queries including MCP
        results = await firecrawl_search(q, limit=3)
        print(f"  [FIRECRAWL] query='{q}' -> {len(results)} results")
        all_results.extend(results)
        for r in results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(r)
        await asyncio.sleep(0.5)  # rate-limit courtesy

    print(f"  [FIRECRAWL] Total unique URLs: {len(unique_results)}")
    for r in unique_results:
        print(f"    - {r.get('url', 'N/A')}")

    # Infer website if not provided
    if website in ("unknown.com", "", None):
        website = _infer_website(unique_results, app_name)
        print(f"  [WEBSITE] Inferred website: {website}")

    # Deep scraping on top 2 unique URLs (preferring docs)
    scraped_contents = {}
    if unique_results:
        # Sort to prioritize URLs with docs/api in them
        sorted_results = sorted(unique_results, key=lambda x: (
            "docs" not in x.get("url", "").lower(),
            "api" not in x.get("url", "").lower()
        ))
        top_urls = [r.get("url", "") for r in sorted_results[:2] if r.get("url")]
        print(f"  [2b/6] Deep scraping {len(top_urls)} URLs: {top_urls}")
        scrape_tasks = [firecrawl_scrape(url) for url in top_urls]
        scraped_texts = await asyncio.gather(*scrape_tasks, return_exceptions=True)
        for url, text in zip(top_urls, scraped_texts):
            if isinstance(text, str) and text.strip():
                scraped_contents[url] = text
                print(f"  [SCRAPE] {url} -> {len(text)} chars")
            elif isinstance(text, Exception):
                print(f"  [SCRAPE] {url} -> FAILED: {text}")
            else:
                print(f"  [SCRAPE] {url} -> empty response")

    context = _build_context(unique_results, scraped_contents)
    evidence = _extract_evidence(unique_results, app_name, website)
    print(f"  [CONTEXT] Total context length: {len(context)} chars, evidence items: {len(evidence)}")

    if not context.strip():
        print(f"  [!] No search results for {app_name}. Marking as UNKNOWN.")
        return AppResearch(
            app_name=app_name,
            category=category,
            website=website,
            api=API(api_available="unknown", api_types=[], api_breadth="unknown"),
            authentication=Authentication(auth_methods=[], developer_access="unknown"),
            webhooks=Webhooks(available="unknown"),
            mcp=MCP(status="unknown"),
            documentation=Documentation(quality="unknown", official_docs=[]),
            composio=ComposioStatus(currently_supported="unknown"),
            recommendation=Recommendation(
                buildability="UNKNOWN", priority="NEEDS_REVIEW",
                score=0, confidence=0,
                recommendation_reason="No search results obtained. Manual research needed."
            ),
            verification=Verification(verified=False, issues=["No data"], verifier_notes="No search results."),
            evidence=evidence,
        )

    # ── Step 3: LLM extraction (parallel) ──
    print(f"  [3/6] Extracting structured data via Gemini...")
    api_task = research_api(app_name, context)
    auth_task = research_auth(app_name, context)
    mcp_task = research_mcp_webhooks_docs(app_name, context)

    api_res_tuple, auth_res_tuple, mcp_res_tuple = await asyncio.gather(
        api_task, auth_task, mcp_task
    )
    
    api_result, api_error = api_res_tuple
    auth_result, auth_error = auth_res_tuple
    mcp_result = mcp_res_tuple
    
    mcp_obj, webhooks_obj, docs_obj, mcp_error = mcp_result

    errors = []
    if api_error: errors.append(f"API_RESEARCHER: {api_error}")
    if auth_error: errors.append(f"AUTH_RESEARCHER: {auth_error}")
    if mcp_error: errors.append(f"MCP_RESEARCHER: {mcp_error}")

    # Log researcher outcomes
    print(f"  [API_RESEARCHER]  result={'SUCCESS: ' + str(api_result.api_available) if api_result else 'FAILED (None)'}")
    print(f"  [AUTH_RESEARCHER] result={'SUCCESS: methods=' + str(auth_result.auth_methods) if auth_result else 'FAILED (None)'}")
    print(f"  [MCP_RESEARCHER]  result={'SUCCESS' if mcp_obj.status != 'unknown' or not mcp_error else 'FAILED (None)'}")

    # Defaults for failed extractions
    if api_result is None:
        api_result = API(api_available="unknown", api_types=[], api_breadth="unknown")
    if auth_result is None:
        auth_result = Authentication(auth_methods=[], developer_access="unknown")

    # ── Step 4: Composio coverage ──
    print(f"  [4/6] Checking Composio toolkit catalog...")
    composio_dict = await check_composio_coverage(app_name)
    composio_status = ComposioStatus(**composio_dict)
    print(f"  [COMPOSIO] result={composio_dict}")

    # ── Step 5: Verification ──
    print(f"  [5/6] Verifying claims...")
    verification, verifier_error = await verify_research(
        app_name=app_name,
        evidence=evidence,
        api_available=api_result.api_available,
        api_types=str(api_result.api_types),
        auth_methods=str(auth_result.auth_methods),
        developer_access=auth_result.developer_access,
        mcp_status=mcp_obj.status,
        webhooks=webhooks_obj.available,
    )
    if verifier_error:
        errors.append(f"VERIFIER: {verifier_error}")
    print(f"  [VERIFIER] status={verification.status}, issues={verification.issues}, unsupported={verification.unsupported_claims}")

    # ── Step 6: Deterministic scoring ──
    print(f"  [6/6] Scoring...")
    app_research = AppResearch(
        app_name=app_name,
        category=category,
        website=website,
        api=api_result,
        authentication=auth_result,
        webhooks=webhooks_obj,
        mcp=mcp_obj,
        documentation=docs_obj,
        composio=composio_status,
        evidence=evidence,
        verification=verification,
        errors=errors,
    )

    # Use deterministic scorer to assemble base recommendation
    base_rec = generate_recommendation(app_research)
    print(f"  [SCORER] score={base_rec.score}, buildability={base_rec.buildability}, priority={base_rec.priority}")

    # Analyst reason (qualitative LLM interpretation)
    composio_sup = composio_status.currently_supported or "no"
    reason = await generate_analyst_reason(
        app_name=app_name,
        category=category,
        api_available=api_result.api_available,
        api_types=str(api_result.api_types),
        api_breadth=api_result.api_breadth,
        auth_methods=str(auth_result.auth_methods),
        developer_access=auth_result.developer_access,
        webhooks=webhooks_obj.available,
        mcp_status=mcp_obj.status,
        doc_quality=docs_obj.quality,
        composio_status=composio_sup,
        buildability=base_rec.buildability,
        score=base_rec.score,
        verification_status=verification.status,
    )

    base_rec.recommendation_reason = reason
    app_research.recommendation = base_rec

    print(f"  [RESULT] {app_name}: {base_rec.buildability} | Score {base_rec.score} | {base_rec.priority}")
    print(f"{'='*60}\n")
    return app_research
