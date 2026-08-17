import pytest
from backend.schemas import Recommendation

def test_recommendation_validation():
    rec = Recommendation(
        buildability="GREEN",
        priority="P0",
        score=95,
        confidence=100,
        recommendation_reason="Excellent API"
    )
    assert rec.score == 95
