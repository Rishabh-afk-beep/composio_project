import pytest
from backend.schemas import AppResearch, API

def test_api_schema():
    api = API(api_available="yes", api_types=["REST"], api_breadth="high", official_api_docs_url="https://docs.example.com")
    assert api.api_available == "yes"
    assert "REST" in api.api_types

def test_app_research_schema():
    app = AppResearch(app_name="TestApp", category="CRM", website="test.com")
    assert app.app_name == "TestApp"
    assert app.evidence == []
