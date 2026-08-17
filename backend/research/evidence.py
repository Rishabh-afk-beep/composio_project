from typing import List, Dict
from backend.schemas import Evidence

def extract_evidence_from_sources(claims: List[Dict], app_name: str) -> List[Evidence]:
    # Placeholder for a utility that maps AI extractions to Evidence schema
    evidences = []
    for c in claims:
        try:
            ev = Evidence(
                field=c.get('field', 'unknown'),
                claim=c.get('claim', 'unknown'),
                source_url=c.get('source_url', ''),
                source_title=c.get('source_title', ''),
                source_type=c.get('source_type', 'secondary'),
                evidence_excerpt=c.get('evidence_excerpt', '')
            )
            evidences.append(ev)
        except Exception as e:
            print(f"Failed to parse evidence: {e}")
    return evidences
