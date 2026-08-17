"""
MCP Researcher – checks for MCP (Model Context Protocol) server availability.
Also extracts webhooks and documentation quality from context.
"""
from backend.agents.llm import safe_ask_llm
from backend.schemas import MCP, Webhooks, Documentation
from pydantic import BaseModel
from typing import Optional, List


class MCPWebhookDocExtraction(BaseModel):
    mcp_status: str  # official / vendor / community / none_found / unknown
    mcp_source_url: Optional[str] = None
    webhooks_available: str  # yes / no / unknown
    webhooks_docs_url: Optional[str] = None
    doc_quality: str  # weak / medium / strong / unknown
    official_docs: List[str]


PROMPT_TEMPLATE = """You are an expert technical analyst. Given the following web research about "{app_name}", extract MCP, webhooks, and documentation information.

WEB RESEARCH CONTENT:
{context}

Extract ONLY what is directly supported by the text above.

MCP = Model Context Protocol. An MCP server allows AI agents/LLMs to interact with the app.
- "official" = the vendor themselves published an MCP server
- "vendor" = a recognized partner/vendor published it
- "community" = a community member published it (e.g. npm package, GitHub repo)
- "none_found" = no MCP server was found in the research
- "unknown" = unclear

Return a JSON object with:
- mcp_status: one of "official", "vendor", "community", "none_found", "unknown"
- mcp_source_url: URL to the MCP server repo/package, or null
- webhooks_available: "yes", "no", or "unknown"
- webhooks_docs_url: URL to webhook docs, or null
- doc_quality: "strong" if comprehensive official docs exist, "medium" if docs exist but limited, "weak" if minimal/poor, "unknown"
- official_docs: list of URLs to official documentation pages found (max 3)
"""


async def research_mcp_webhooks_docs(app_name: str, context: str):
    """Returns (MCP, Webhooks, Documentation, error_str_or_None) tuple."""
    prompt = PROMPT_TEMPLATE.format(app_name=app_name, context=context)
    result, error = await safe_ask_llm(prompt, schema=MCPWebhookDocExtraction, label="MCP_RESEARCHER")

    if result is None:
        return (
            MCP(status="unknown"),
            Webhooks(available="unknown"),
            Documentation(quality="unknown", official_docs=[]),
            error
        )

    return (
        MCP(status=result.mcp_status, source_url=result.mcp_source_url),
        Webhooks(available=result.webhooks_available, docs_url=result.webhooks_docs_url),
        Documentation(quality=result.doc_quality, official_docs=result.official_docs),
        error
    )
