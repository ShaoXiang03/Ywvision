"""
Focus market selection logic (1 crypto + 1 sports)
"""
from typing import List, Dict, Optional

from src.core.models import MarketRecord
from src.core.filters import is_crypto_market, is_sports_market


def select_focus_markets(candidates: List[MarketRecord]) -> Dict[str, Optional[MarketRecord]]:
    """
    Select focus markets: 1 crypto + 1 sports
    
    Strategy:
    - Select first crypto market from candidates
    - Select first sports market from candidates
    - Both must be within 48h window (already filtered in candidates)
    
    Args:
        candidates: List of candidate markets (already filtered)
    
    Returns:
        Dictionary with 'crypto' and 'sports' keys
    """
    crypto_market = None
    sports_market = None
    
    for market in candidates:
        # Find first crypto market
        if crypto_market is None and is_crypto_market(market):
            crypto_market = market
        
        # Find first sports market
        if sports_market is None and is_sports_market(market):
            sports_market = market
        
        # Stop if we found both
        if crypto_market and sports_market:
            break
    
    return {
        'crypto': crypto_market,
        'sports': sports_market
    }   