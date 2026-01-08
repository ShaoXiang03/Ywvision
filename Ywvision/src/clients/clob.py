"""
CLOB API Client for Polymarket (public methods only)
"""
import requests
from typing import List, Dict, Optional


class ClobClient:
    """Client for Polymarket CLOB API (public endpoints)"""
    
    BASE_URL = "https://clob.polymarket.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Polymarket-Dashboard/1.0"
        })
    
    def get_prices(
        self,
        tokens: List[str],
        side: str = "buy"  # "buy" for best ask (market buy price), "sell" for best bid
    ) -> Dict[str, Optional[float]]:
        """
        Batch fetch best prices for tokens (public, no auth)
        
        Args:
            tokens: List of token IDs (e.g., YES/NO clobTokenIds)
            side: "buy" (best ask) or "sell" (best bid)
        
        Returns:
            Dict of token_id: price (float or None if no orders)
        """
        if not tokens:
            return {}
        
        url = f"{self.BASE_URL}/prices"
        payload = {
            "tokens": tokens,
            "side": side.lower()
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Convert str prices to float, null to None
            return {k: float(v) if v is not None else None for k, v in data.items()}
        except requests.RequestException as e:
            print(f"Error fetching CLOB prices: {e}")
            return {}
    
    # Optional: Add GET /book for full order book if needed later
    def get_order_book(self, token_id: str) -> Optional[Dict]:
        """
        Fetch full order book for a single token
        
        Args:
            token_id: Token identifier
        
        Returns:
            Dict with 'bids' and 'asks' or None
        """
        url = f"{self.BASE_URL}/book"
        params = {"token_id": token_id}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching order book for {token_id}: {e}")
            return None