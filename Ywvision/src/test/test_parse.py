"""
Unit tests for market parsing
"""
import json
from datetime import datetime, timedelta

from src.core.parse import parse_market, parse_json_field, find_outcome_index


def test_parse_json_field_with_string():
    """Test parsing JSON string field"""
    json_str = '["Yes", "No"]'
    result = parse_json_field(json_str)
    assert result == ["Yes", "No"]


def test_parse_json_field_with_list():
    """Test parsing field that's already a list"""
    list_field = ["Yes", "No"]
    result = parse_json_field(list_field)
    assert result == ["Yes", "No"]


def test_parse_json_field_with_none():
    """Test parsing None field"""
    result = parse_json_field(None)
    assert result is None


def test_find_outcome_index():
    """Test finding outcome index"""
    outcomes = ["Yes", "No"]
    
    yes_idx = find_outcome_index(outcomes, "yes")
    assert yes_idx == 0
    
    no_idx = find_outcome_index(outcomes, "no")
    assert no_idx == 1
    
    invalid = find_outcome_index(outcomes, "maybe")
    assert invalid is None


def test_parse_market_basic():
    """Test parsing a basic valid market"""
    future_date = (datetime.now() + timedelta(hours=24)).isoformat()
    
    raw_market = {
        "id": "test-market-123",
        "slug": "test-market",
        "question": "Will this test pass?",
        "category": "Testing",
        "endDate": future_date,
        "enableOrderBook": True,
        "active": True,
        "closed": False,
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.55", "0.45"],
        "clobTokenIds": ["token-yes-123", "token-no-456"]
    }
    
    market = parse_market(raw_market)
    
    assert market is not None
    assert market.id == "test-market-123"
    assert market.question == "Will this test pass?"
    assert market.yes_token_id == "token-yes-123"
    assert market.no_token_id == "token-no-456"
    assert market.yes_price == 0.55
    assert market.no_price == 0.45
    assert market.invalid_reason is None


def test_parse_market_with_json_strings():
    """Test parsing market with JSON string fields"""
    future_date = (datetime.now() + timedelta(hours=24)).isoformat()
    
    raw_market = {
        "id": "test-market-456",
        "question": "Test with JSON strings",
        "category": "Testing",
        "endDate": future_date,
        "enableOrderBook": True,
        "active": True,
        "closed": False,
        "outcomes": '["Yes", "No"]',  # JSON string
        "outcomePrices": '["0.60", "0.40"]',  # JSON string
        "clobTokenIds": '["token-1", "token-2"]'  # JSON string
    }
    
    market = parse_market(raw_market)
    
    assert market is not None
    assert market.yes_token_id == "token-1"
    assert market.no_token_id == "token-2"
    assert market.yes_price == 0.60
    assert market.no_price == 0.40


def test_parse_market_not_binary():
    """Test parsing non-binary market"""
    future_date = (datetime.now() + timedelta(hours=24)).isoformat()
    
    raw_market = {
        "id": "test-market-789",
        "question": "Which team will win?",
        "category": "Sports",
        "endDate": future_date,
        "enableOrderBook": True,
        "active": True,
        "closed": False,
        "outcomes": ["Team A", "Team B", "Team C"],  # 3 outcomes
        "outcomePrices": ["0.33", "0.33", "0.34"],
        "clobTokenIds": ["token-1", "token-2", "token-3"]
    }
    
    market = parse_market(raw_market)
    
    assert market is not None
    assert market.invalid_reason is not None
    assert "Not a binary market" in market.invalid_reason


if __name__ == "__main__":
    # Run tests
    test_parse_json_field_with_string()
    test_parse_json_field_with_list()
    test_parse_json_field_with_none()
    test_find_outcome_index()
    test_parse_market_basic()
    test_parse_market_with_json_strings()
    test_parse_market_not_binary()
    
    print("✅ All tests passed!")