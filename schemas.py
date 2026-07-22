from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ModelMetricsResponse(BaseModel):
    accuracy: float
    precision: float
    recall: float
    feature_importances: Dict[str, float]

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

class CandlePoint(BaseModel):
    x: str
    y: List[float] = Field(..., description="[Open, High, Low, Close]")

class CandlestickResponse(BaseModel):
    ticker: str
    total_candles: int
    series: List[CandlePoint]

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


# --- Existing Schemas (ModelMetricsResponse, TickerSummary, etc.) ---

# --- JWT & Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    is_active: bool = True

class UserInDB(UserResponse):
    hashed_password: str