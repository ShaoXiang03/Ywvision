"""
# In parse_market, after extracting yes_price/no_price from outcomePrices:
# (No code change needed here—keep as is for fallback)
Market data parsing and standardization
"""
import json
from datetime import datetime
from typing import Dict, Optional, List, Any

from src.core.models import MarketRecord


def parse_market(raw_market: Dict) -> Optional[MarketRecord]:
    """
    Parse and standardize a raw market from Gamma API
    
    Args:
        raw_market: Raw market data from API
    
    Returns:
        MarketRecord or None if parsing fails critically
    """
    try:
        # Extract basic fields
        market_id = raw_market.get('id') or raw_market.get('conditionId')
        if not market_id:
            return None
        
        # Parse outcomes (may be string or array)
        outcomes = parse_json_field(raw_market.get('outcomes'))
        
        # Parse outcomePrices (may be string or array)
        outcome_prices = parse_json_field(raw_market.get('outcomePrices'))
        
        # Parse clobTokenIds (may be string or array)
        clob_token_ids = parse_json_field(raw_market.get('clobTokenIds'))
        
        # Calculate hours to close
        hours_to_close = calculate_hours_to_close(raw_market.get('endDate'))
        
        # Identify YES/NO tokens and prices
        yes_token_id, no_token_id = None, None
        yes_price, no_price = None, None
        invalid_reason = None
        
        if outcomes and clob_token_ids:
            if not isinstance(outcomes, list) or not isinstance(clob_token_ids, list):
                invalid_reason = "outcomes or clobTokenIds not a list"
            elif len(outcomes) != 2:
                invalid_reason = f"Not a binary market (outcomes count: {len(outcomes)})"
            elif len(clob_token_ids) != len(outcomes):
                invalid_reason = "clobTokenIds length mismatch with outcomes"
            else:
                # Try to identify YES and NO
                yes_idx = find_outcome_index(outcomes, 'yes')
                no_idx = find_outcome_index(outcomes, 'no')
                
                if yes_idx is None or no_idx is None:
                    invalid_reason = "Cannot identify YES/NO outcomes"
                else:
                    yes_token_id = clob_token_ids[yes_idx]
                    no_token_id = clob_token_ids[no_idx]
                    
                    # Extract prices if available
                    if outcome_prices and isinstance(outcome_prices, list):
                        if len(outcome_prices) >= len(outcomes):
                            try:
                                yes_price = float(outcome_prices[yes_idx])
                            except (ValueError, TypeError):
                                pass
                            
                            try:
                                no_price = float(outcome_prices[no_idx])
                            except (ValueError, TypeError):
                                pass
        else:
            invalid_reason = "Missing outcomes or clobTokenIds"
        
        # Create MarketRecord
        return MarketRecord(
            id=market_id,
            slug=raw_market.get('slug'),
            question=raw_market.get('question'),
            category=raw_market.get('category'),
            endDate=raw_market.get('endDate'),
            hours_to_close=hours_to_close,
            enableOrderBook=raw_market.get('enableOrderBook', False),
            active=raw_market.get('active', False),
            closed=raw_market.get('closed', False),
            yes_token_id=yes_token_id,
            no_token_id=no_token_id,
            yes_price=yes_price,
            no_price=no_price,
            invalid_reason=invalid_reason
        )
    
    except Exception as e:
        print(f"Error parsing market: {e}")
        return None


def parse_json_field(field: Any) -> Optional[List]:
    """
    Parse a field that may be a JSON string or already a list
    
    Args:
        field: Field value (string, list, or other)
    
    Returns:
        Parsed list or None
    """
    if field is None:
        return None
    
    if isinstance(field, list):
        return field
    
    if isinstance(field, str):
        try:
            parsed = json.loads(field)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
    
    return None


def calculate_hours_to_close(end_date_str: Optional[str]) -> Optional[float]:
    """
    Calculate hours until market closes
    
    Args:
        end_date_str: End date in ISO format
    
    Returns:
        Hours to close (rounded to 2 decimals) or None
    """
    if not end_date_str:
        return None
    
    try:
        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        now = datetime.now(end_date.tzinfo)
        
        hours = (end_date - now).total_seconds() / 3600
        return round(hours, 2)
    except (ValueError, AttributeError) as e:
        print(f"Error calculating hours to close: {e}")
        return None


def find_outcome_index(outcomes: List[str], keyword: str) -> Optional[int]:
    """
    Find index of outcome containing keyword (case-insensitive)
    
    Args:
        outcomes: List of outcome strings
        keyword: Keyword to search for
    
    Returns:
        Index or None if not found
    """
    keyword_lower = keyword.lower()
    
    for i, outcome in enumerate(outcomes):
        if outcome and keyword_lower in str(outcome).lower():
            return i
    
    return None