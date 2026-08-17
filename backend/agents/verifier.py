"""
Verification Agent – challenges extracted claims against evidence.
"""
from backend.agents.llm import safe_ask_llm
from backend.schemas import Verification, Evidence
from typing import List


PROMPT_TEMPLATE = """You are a rigorous fact-checker for a developer API research project about "{app_name}".

Below are the claims and evidence collected. Your job is to verify:
1. Is there actual evidence supporting each claim?
2. Are sources official (developer docs, official site, official GitHub)?
3. Is "API existence" confused with "API access"? (An API may exist but require enterprise access)
4. Is "self-serve access" confused with "enterprise/partner access"?
5. Is "official MCP" confused with "community MCP"?

EVIDENCE:
{evidence_text}

CLAIMS SUMMARY:
- API available: {api_available}
- API types: {api_types}
- Auth methods: {auth_methods}
- Developer access: {developer_access}
- MCP status: {mcp_status}
- Webhooks: {webhooks}

Return a JSON object:
- status: "verified" if the overall picture is consistent and evidence-backed, "rejected" if there are significant issues
- unsupported_claims: list of claim categories (e.g., "api_available", "auth_methods", "webhooks", "mcp_status") that are completely contradicted or lack any evidence. Leave empty if all are supported.
- issues: list of strings describing each problem found (empty list if none)
- verifier_notes: a short summary of your verification assessment
"""


async def verify_research(
    app_name: str,
    evidence: List[Evidence],
    api_available: str = "unknown",
    api_types: str = "[]",
    auth_methods: str = "[]",
    developer_access: str = "unknown",
    mcp_status: str = "unknown",
    webhooks: str = "unknown",
) -> Verification:
    evidence_text = ""
    for e in evidence[:10]:  # limit to 10 evidence items
        evidence_text += f"- [{e.source_type}] {e.field}: \"{e.claim}\" (source: {e.source_url})\n"
        if e.evidence_excerpt:
            evidence_text += f"  Excerpt: {e.evidence_excerpt[:150]}\n"

    if not evidence_text.strip():
        evidence_text = "No evidence collected."

    prompt = PROMPT_TEMPLATE.format(
        app_name=app_name,
        evidence_text=evidence_text,
        api_available=api_available,
        api_types=api_types,
        auth_methods=auth_methods,
        developer_access=developer_access,
        mcp_status=mcp_status,
        webhooks=webhooks,
    )

    result, error = await safe_ask_llm(prompt, schema=Verification, label="VERIFIER")
    if result is None:
        return Verification(
            status="unavailable",
            issues=["Verification LLM call failed"],
            verifier_notes="Could not run verification – LLM unavailable.",
        ), error
    
    # Map the old boolean from the LLM schema to the new status string.
    # The prompt actually returns verified as boolean, so we map it.
    final_status = "verified" if result.status == "True" or result.status == "true" or getattr(result, "verified", False) else "rejected"
    # Actually wait, I need to update PROMPT_TEMPLATE and the Verification schema the LLM is using.
    # I will just set status = result.status if it exists, otherwise map from result.verified if the old schema was used.
    
    return result, error
