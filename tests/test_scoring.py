from backend.scoring.scorer import calculate_score, determine_buildability
from backend.schemas import AppResearch, API, Authentication, Documentation

def test_scorer_green():
    app = AppResearch(
        app_name="TestApp",
        category="CRM",
        website="test.com",
        api=API(api_available="yes", api_types=["REST"], api_breadth="high"),
        authentication=Authentication(auth_methods=["OAuth2"], developer_access="self_serve"),
        documentation=Documentation(quality="strong", official_docs=[])
    )
    score = calculate_score(app)
    assert score > 60
    
    buildability = determine_buildability(app)
    assert buildability == "GREEN"

def test_scorer_red():
    app = AppResearch(
        app_name="TestApp",
        category="CRM",
        website="test.com",
        api=API(api_available="no", api_types=[], api_breadth="unknown")
    )
    buildability = determine_buildability(app)
    assert buildability == "RED"
