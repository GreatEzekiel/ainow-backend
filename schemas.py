from typing import List, Optional
from pydantic import BaseModel, EmailStr

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

class MarketMetricsResponse(BaseModel):
    latest_date: str
    market_avg_price: float
    market_open_avg: float
    market_close_avg: float
    market_return_pct: float
    synthetic_asi: float

class TickerSummary(BaseModel):
    ticker: str
    open_price: float
    close_price: float
    high_price: float
    low_price: float
    change_pct: float
    vs_market_avg: float
    rsi_14: float
    sma_10: float
    sma_20: float
    prediction: int
    prediction_label: str
    confidence: int

class CandlestickPoint(BaseModel):
    x: str
    y: List[float]

class CandlestickResponse(BaseModel):
    ticker: str
    total_candles: int
    series: List[CandlestickPoint]

class InferenceRequest(BaseModel):
    ticker: str
    open_price: float
    close_price: float
    daily_return: float
    rsi_14: float
    sma_10: float
    sma_20: float

class InferenceResponse(BaseModel):
    ticker: str
    prediction: int
    prediction_label: str
    confidence: float