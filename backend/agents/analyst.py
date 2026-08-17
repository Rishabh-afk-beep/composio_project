"""
Product Analyst – interprets structured evidence and produces a human-readable recommendation.
The actual numeric scoring is done deterministically in scorer.py. This agent only provides
the qualitative interpretation and recommendation reason.
"""
from backend.agents.llm import safe_ask_llm
from typing import Optional


PROMPT_TEMPLATE = """You are a product analyst at Composio evaluating whether to build a toolkit for "{app_name}" ({category}).

Here are the research findings:
- API available: {api_available}
- API types: {api_types}
- API breadth: {api_breadth}
- Auth methods: {auth_methods}
- Developer access: {developer_access}
- Webhooks: {webhooks}
- MCP status: {mcp_status}
- Documentation quality: {doc_quality}
- Composio currently supported: {composio_status}
- Buildability: {buildability}
- Score: {score}/100
- Verification: {verification_status}

Write a concise 1-2 sentence recommendation reason explaining why this app should or should not be prioritized for toolkit development. Focus on the key risk or opportunity. Do not use marketing language. Be direct.

Return ONLY the recommendation text, nothing else.
"""


async def generate_analyst_reason(
    app_name: str,
    category: str,
    api_available: str,
    api_types: str,
    api_breadth: str,
    auth_methods: str,
    developer_access: str,
    webhooks: str,
    mcp_status: str,
    doc_quality: str,
    composio_status: str,
    buildability: str,
    score: int,
    verification_status: str,
) -> str:
    prompt = PROMPT_TEMPLATE.format(
        app_name=app_name,
        category=category,
        api_available=api_available,
        api_types=api_types,
        api_breadth=api_breadth,
        auth_methods=auth_methods,
        developer_access=developer_access,
        webhooks=webhooks,
        mcp_status=mcp_status,
        doc_quality=doc_quality,
        composio_status=composio_status,
        buildability=buildability,
        score=score,
        verification_status=verification_status,
    )

    result, error = await safe_ask_llm(prompt, schema=None, label="ANALYST")
    if not result:
        return f"Could not generate analyst reason due to error: {error}"
    
    return result.strip().strip('"')
