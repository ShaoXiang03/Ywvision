"""
Data Models for Polymarket Markets
"""
from typing import Optional
from pydantic import BaseModel, Field


class MarketRecord(BaseModel):
    """Standardized market record"""
    
    id: str = Field(..., description="Market unique identifier")
    slug: Optional[str] = Field(None, description="Market URL slug")
    question: Optional[str] = Field(None, description="Market question")
    category: Optional[str] = Field(None, description="Market category")
    endDate: Optional[str] = Field(None, description="End date (ISO format)")
    hours_to_close: Optional[float] = Field(None, description="Hours until market closes")
    
    enableOrderBook: bool = Field(False, description="Order book enabled")
    active: bool = Field(False, description="Market is active")
    closed: bool = Field(False, description="Market is closed")
    
    yes_token_id: Optional[str] = Field(None, description="YES outcome token ID")
    no_token_id: Optional[str] = Field(None, description="NO outcome token ID")
    
    yes_price: Optional[float] = Field(None, description="YES outcome price")
    no_price: Optional[float] = Field(None, description="NO outcome price")
    
    invalid_reason: Optional[str] = Field(None, description="Reason if market is invalid")
    
    class Config:
        frozen = False  # Allow modifications after creation