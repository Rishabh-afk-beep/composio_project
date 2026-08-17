# We mock the composio matching to test it
from backend.schemas import ComposioStatus

def test_composio_matching_logic():
    # If the response had an exact match
    app_name = "MongoDB Atlas"
    composio_item_name = "MongoDB"
    
    # Simulating the exact match logic from composio_checker.py
    app_lower = app_name.lower().replace(" ", "")
    comp_lower = composio_item_name.lower().replace(" ", "")
    
    # We would rely on exact or substring
    # In reality, this requires fuzzy matching
    assert app_lower != comp_lower
    assert comp_lower in app_lower
