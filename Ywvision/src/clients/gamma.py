"""
Gamma Markets API Client
"""
import requests
from typing import List, Dict, Optional


class GammaClient:
    """Client for Polymarket Gamma Markets API"""
    
    BASE_URL = "https://gamma-api.polymarket.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Polymarket-Dashboard/1.0"
        })
    
    def get_markets(
        self, 
        limit: int = 100, 
        offset: int = 0,
        closed: Optional[bool] = None
    ) -> List[Dict]:
        """
        Fetch markets from Gamma API
        
        Args:
            limit: Number of markets to fetch (default: 100)
            offset: Pagination offset (default: 0)
            closed: Filter by closed status (optional)
        
        Returns:
            List of market dictionaries
        """
        url = f"{self.BASE_URL}/markets"
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if closed is not None:
            params["closed"] = str(closed).lower()
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching markets: {e}")
            return []
    
    def get_market_by_id(self, market_id: str) -> Optional[Dict]:
        """
        Fetch a single market by ID
        
        Args:
            market_id: Market identifier
        
        Returns:
            Market dictionary or None if not found
        """
        url = f"{self.BASE_URL}/markets/{market_id}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching market {market_id}: {e}")
            return None