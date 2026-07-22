from typing import List, Dict, Optional
from pydantic import BaseModel, EmailStr, Field

# --- Auth & User Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool = True

    class Config:
        from_attributes = True

class UserInDB(UserResponse):
    hashed_password: str

# --- Market & Prediction Schemas ---
class ModelMetricsResponse(BaseModel):
    accuracy: float
    precision: float
    recall: float
    feature_importances: Dict[str, float]

class MarketMetricsResponse(BaseModel):
    latest_date: str
    avg_open: float
    avg_close: float
    avg_return: float
    synthetic_ngx_asi: float

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
    confidence: float

class CandlestickPoint(BaseModel):
    x: str
    y: List[float] = Field(..., description="[Open, High, Low, Close]")

class CandlestickResponse(BaseModel):
    ticker: str
    total_candles: int
    series: List[CandlestickPoint]

class InferenceRequest(BaseModel):
    ticker: str

class InferenceResponse(BaseModel):
    ticker: str
    prediction: int
    prediction_label: str
    confidence: float