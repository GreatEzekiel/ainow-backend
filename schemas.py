from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# --- User Schemas ---
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Stock & Analytics Schemas ---
class TickerSummary(BaseModel):
    ticker: str
    last_price: float
    daily_return: float
    rsi_14: Optional[float] = None
    prediction: Optional[int] = None  # 1 = Rise, 0 = Fall

class PricePoint(BaseModel):
    date: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    sma_10: Optional[float] = None
    sma_20: Optional[float] = None
    rsi_14: Optional[float] = None

    class Config:
        from_attributes = True

class PredictRequest(BaseModel):
    ticker: str
    open_price: float
    close_price: float
    daily_return: float
    rsi_14: float
    sma_10: float
    sma_20: float

class PredictResponse(BaseModel):
    ticker: str
    prediction: int
    label: str
    confidence: float