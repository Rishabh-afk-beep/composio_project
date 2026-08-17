"""
API Researcher – extracts API availability, types, breadth from raw context.
"""
from backend.agents.llm import safe_ask_llm
from backend.schemas import API
from typing import Optional


PROMPT_TEMPLATE = """You are an expert technical analyst. Given the following web research about "{app_name}", extract API information.

WEB RESEARCH CONTENT:
{context}

Extract ONLY what is directly supported by the text above. If the text does not mention something, use "unknown".

Return a JSON object with exactly these fields:
- api_available: "yes" if there is a public developer API, "no" if explicitly stated none exists, "unknown" if unclear
- api_types: list of strings like "REST", "GraphQL", "SOAP", "SDK", "CLI", "WebSocket" — empty list if unknown
- api_breadth: "high" if comprehensive with many endpoints, "medium" if moderate, "low" if limited, "unknown" if unclear
- official_api_docs_url: string URL to official API docs, or null if not found
"""


async def research_api(app_name: str, context: str) -> tuple[Optional[API], Optional[str]]:
    prompt = PROMPT_TEMPLATE.format(app_name=app_name, context=context)
    result, error = await safe_ask_llm(prompt, schema=API, label="API_RESEARCHER")
    return result, error
