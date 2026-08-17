"""
Auth Researcher – extracts authentication methods and developer access from raw context.
"""
from backend.agents.llm import safe_ask_llm
from backend.schemas import Authentication
from typing import Optional


PROMPT_TEMPLATE = """You are an expert technical analyst. Given the following web research about "{app_name}", extract authentication and developer access information.

WEB RESEARCH CONTENT:
{context}

Extract ONLY what is directly supported by the text above. If the text does not mention something, use "unknown".

Return a JSON object with exactly these fields:
- auth_methods: list of strings like "OAuth2", "API Key", "PAT", "JWT", "Basic Auth", "Bearer Token" — empty list if unknown
- developer_access: one of "self_serve", "paid_plan", "approval_required", "partner_gated", "private", "unknown"
  - "self_serve" means any developer can sign up and get credentials
  - "paid_plan" means API access requires a paid plan
  - "approval_required" means you need to apply/be approved
  - "partner_gated" means access is restricted to partners
  - "private" means no developer access available
  - "unknown" if unclear
- auth_docs_url: string URL to official auth documentation, or null if not found
"""


async def research_auth(app_name: str, context: str) -> tuple[Optional[Authentication], Optional[str]]:
    prompt = PROMPT_TEMPLATE.format(app_name=app_name, context=context)
    result, error = await safe_ask_llm(prompt, schema=Authentication, label="AUTH_RESEARCHER")
    return result, error
