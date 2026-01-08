"""
Market filtering logic
"""
from typing import List

from src.core.models import MarketRecord


def filter_candidates(markets: List[MarketRecord], max_hours: float = 168) -> List[MarketRecord]:
    """
    Filter markets to get candidates based on requirements:
    1. enableOrderBook == True
    2. active == True and closed == False
    3. 0 < hours_to_close <= max_hours (default 168 = 7 days)
    4. Has valid YES/NO token IDs
    
    Args:
        markets: List of MarketRecord objects
        max_hours: Maximum hours until close (default 168 for 7 days)
    
    Returns:
        Filtered list of candidate markets
    """
    candidates = []
    
    for market in markets:
        # Check enableOrderBook
        if not market.enableOrderBook:
            continue
        
        # Check active and not closed
        if not market.active or market.closed:
            continue
        
        # Check hours_to_close (0 < x <= max_hours)
        if market.hours_to_close is None:
            continue
        if not (0 < market.hours_to_close <= max_hours):
            continue
        
        # Check valid YES/NO token IDs
        if not market.yes_token_id or not market.no_token_id:
            continue
        
        candidates.append(market)
    
    return candidates


def filter_valid_prices(markets: List[MarketRecord]) -> List[MarketRecord]:
    """
    Filter markets with valid YES and NO prices
    
    A price is valid if it is not None and is a valid number
    
    Args:
        markets: List of MarketRecord objects
    
    Returns:
        Filtered list with valid prices
    """
    return [
        m for m in markets
        if m.yes_price is not None 
        and m.no_price is not None
        and not isinstance(m.yes_price, type(None))
        and not isinstance(m.no_price, type(None))
    ]


def is_crypto_market(market: MarketRecord) -> bool:
    """
    Check if market is a crypto market
    
    Rule: category contains "crypto" (case-insensitive)
    
    Args:
        market: MarketRecord object
    
    Returns:
        True if crypto market
    """
    if not market.category:
        return False
    return 'crypto' in market.category.lower()


def is_sports_market(market: MarketRecord) -> bool:
    """
    Check if market is a sports market
    
    Rule: category contains "sports" (case-insensitive)
    
    Args:
        market: MarketRecord object
    
    Returns:
        True if sports market
    """
    if not market.category:
        return False
    return 'sports' in market.category.lower()