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
    Detect crypto markets reliably:
    - API category contains 'crypto' (case-insensitive)
    - OR question contains common crypto keywords
    """
    if market.category and 'crypto' in market.category.lower():
        return True
    
    if market.question:
        crypto_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'sol', 'xrp',
            'crypto', 'binance', 'coinbase', 'hyperliquid', 'okx', 'megaeth'
        ]
        return any(keyword in market.question.lower() for keyword in crypto_keywords)
    
    return False


def is_sports_market(market: MarketRecord) -> bool:
    """
    Detect sports markets reliably:
    - API category contains 'sports'
    - OR question contains common sports keywords
    """
    if market.category and 'sports' in market.category.lower():
        return True
    
    if market.question:
        sports_keywords = [
            'nfl', 'nba', 'afc', 'nfc', 'super bowl', 'championship',
            'eagles', 'packers', 'rams', 'bears', 'chiefs', 'rams', 'seahawks',
            'football', 'basketball', 'soccer', 'world cup'
        ]
        return any(keyword in market.question.lower() for keyword in sports_keywords)
    
    return False