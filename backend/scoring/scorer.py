from typing import Dict, Any
from backend.schemas import Recommendation, AppResearch

def calculate_score(app: AppResearch) -> int:
    score = 0
    unsupported = app.verification.unsupported_claims if app.verification and app.verification.status != "verified" else []
    
    # API availability (20)
    if "api_available" not in unsupported and app.api and app.api.api_available.lower() == 'yes':
        score += 20
    
    # Authentication (15)
    if "auth_methods" not in unsupported and app.authentication and app.authentication.auth_methods:
        score += 15
        
    # Developer access (15)
    if app.authentication:
        access = app.authentication.developer_access.lower()
        if access == 'self_serve':
            score += 15
        elif access in ['paid_plan', 'approval_required']:
            score += 5
        elif access == 'partner_gated':
            score += 0
            
    # API breadth (15)
    if app.api:
        breadth = app.api.api_breadth.lower()
        if breadth == 'high':
            score += 15
        elif breadth == 'medium':
            score += 10
        elif breadth == 'low':
            score += 5

    # Webhooks (10)
    if "webhooks" not in unsupported and app.webhooks and app.webhooks.available.lower() == 'yes':
        score += 10
        
    # Documentation quality (10)
    if app.documentation:
        q = app.documentation.quality.lower()
        if q == 'strong':
            score += 10
        elif q == 'medium':
            score += 5
            
    # MCP / agent readiness (5)
    if "mcp_status" not in unsupported and app.mcp:
        status = app.mcp.status.lower()
        if status in ['official', 'vendor']:
            score += 5
        elif status == 'community':
            score += 2
            
    # Strategic utility (10) - Defaulting to 10 for target apps
    score += 10

    return min(score, 100)

def determine_buildability(app: AppResearch) -> str:
    # RED conditions
    if app.api and app.api.api_available.lower() == 'no':
        return 'RED'
    if app.authentication and app.authentication.developer_access.lower() in ['private']:
        return 'RED'
        
    # YELLOW conditions
    if app.authentication and app.authentication.developer_access.lower() in ['paid_plan', 'partner_gated', 'approval_required']:
        return 'YELLOW'
        
    # GREEN conditions
    if (app.api and app.api.api_available.lower() == 'yes' and 
        app.authentication and app.authentication.developer_access.lower() == 'self_serve' and
        app.documentation and app.documentation.quality.lower() in ['strong', 'medium']):
        return 'GREEN'
        
    return 'UNKNOWN'

def determine_priority(score: int, buildability: str, composio_status: str) -> str:
    if composio_status.lower() == 'yes':
        return 'COVERED'
    
    if buildability == 'RED':
        return 'HOLD'
        
    if buildability == 'UNKNOWN':
        return 'NEEDS_REVIEW'

    if score >= 80:
        return 'P0'
    elif score >= 65:
        return 'P1'
    elif score >= 50:
        return 'P2'
    
    return 'HOLD'

def generate_recommendation(app: AppResearch) -> Recommendation:
    score = calculate_score(app)
    buildability = determine_buildability(app)
    
    composio_status = 'no'
    if app.composio and app.composio.currently_supported:
        composio_status = app.composio.currently_supported.lower()
        
    priority = determine_priority(score, buildability, composio_status)
    
    # Simple confidence heuristic based on number of evidence items
    evidence_count = len(app.evidence)
    if app.verification and app.verification.status == "unavailable":
        confidence = 0
    else:
        confidence = min(100, evidence_count * 15 + 20)
    
    reason = f"Score: {score}. Buildability: {buildability}. Priority: {priority}."
    if composio_status == 'yes':
        reason = "Already supported by Composio."
    elif buildability == 'RED':
        reason = "Blocked due to lack of API or private access."
        
    return Recommendation(
        buildability=buildability,
        priority=priority,
        score=score,
        confidence=confidence,
        recommendation_reason=reason
    )
