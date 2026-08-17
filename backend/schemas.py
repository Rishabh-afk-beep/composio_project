from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Evidence(BaseModel):
    field: str
    claim: str
    source_url: str
    source_title: str
    source_type: str  # official_docs, official_site, official_github, official_pricing, secondary, search_result
    evidence_excerpt: str
    checked_at: datetime = Field(default_factory=datetime.utcnow)

class API(BaseModel):
    api_available: str  # yes/no/unknown
    api_types: List[str]
    api_breadth: str  # low/medium/high/unknown
    official_api_docs_url: Optional[str] = None

class Authentication(BaseModel):
    auth_methods: List[str]
    developer_access: str  # self_serve / paid_plan / approval_required / partner_gated / private / unknown
    auth_docs_url: Optional[str] = None

class Webhooks(BaseModel):
    available: str  # yes/no/unknown
    docs_url: Optional[str] = None

class MCP(BaseModel):
    status: str  # official / vendor / community / none_found / unknown
    source_url: Optional[str] = None

class Documentation(BaseModel):
    quality: str  # weak/medium/strong/unknown
    official_docs: List[str]

class ComposioStatus(BaseModel):
    currently_supported: str  # yes / no / unknown
    toolkit_slug: Optional[str] = None
    toolkit_source_url: Optional[str] = None

class Recommendation(BaseModel):
    buildability: str  # GREEN / YELLOW / RED / UNKNOWN
    priority: str  # P0 / P1 / P2 / HOLD
    score: int
    confidence: int
    recommendation_reason: str

class Verification(BaseModel):
    status: str  # verified / rejected / unavailable
    unsupported_claims: List[str] = Field(default_factory=list)
    issues: List[str]
    verifier_notes: str

class AppResearch(BaseModel):
    app_name: str
    category: str
    website: str
    
    api: Optional[API] = None
    authentication: Optional[Authentication] = None
    webhooks: Optional[Webhooks] = None
    mcp: Optional[MCP] = None
    documentation: Optional[Documentation] = None
    composio: Optional[ComposioStatus] = None
    recommendation: Optional[Recommendation] = None
    verification: Optional[Verification] = None
    evidence: List[Evidence] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
