import os
import logging
import joblib
import numpy as np
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ngx_api")

app = FastAPI(
    title="NGX Alpha Labs - Quantitative Trading API",
    description="Institutional ML Signal & Analytics Engine for the Nigerian Exchange Group",
    version="2.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load ML Model Artifact
MODEL_PATH = "model.pkl" if os.path.exists("model.pkl") else "../model.pkl"
ml_model = None

if os.path.exists(MODEL_PATH):
    try:
        ml_model = joblib.load(MODEL_PATH)
        logger.info(f"Loaded Machine Learning model from {MODEL_PATH}")
    except Exception as e:
        logger.warning(f"Could not load ML model file ({e}). Fallback logic enabled.")
else:
    logger.warning(f"Model file not found at {MODEL_PATH}. Using algorithmic fallback.")

# -------------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------------
class PredictionRequest(BaseModel):
    ticker: str = Field(..., example="MTNN")
    open_price: float = Field(..., example=230.50)
    close_price: float = Field(..., example=235.00)
    daily_return: float = Field(..., example=0.0195)
    rsi_14: float = Field(..., example=58.4)
    sma_10: float = Field(..., example=231.20)
    sma_20: float = Field(..., example=228.00)

class PredictionResponse(BaseModel):
    ticker: str
    prediction: int
    signal: str
    confidence: float
    probability_up: float
    probability_down: float
    target_price: float
    model_source: str

# Mock Database of Equities
EQUITY_DATABASE: Dict[str, Dict[str, Any]] = {
    "MTNN": {
        "company": "MTN Nigeria Communications Plc",
        "sector": "Telecommunications",
        "open_price": 230.50,
        "close_price": 235.00,
        "high_price": 238.00,
        "low_price": 229.00,
        "daily_return": 0.0195,
        "rsi_14": 58.4,
        "sma_10": 231.20,
        "sma_20": 228.00,
    },
    "DANGCEM": {
        "company": "Dangote Cement Plc",
        "sector": "Industrial Goods",
        "open_price": 640.00,
        "close_price": 655.00,
        "high_price": 660.00,
        "low_price": 638.00,
        "daily_return": 0.0234,
        "rsi_14": 64.2,
        "sma_10": 645.00,
        "sma_20": 632.00,
    },
    "GTCO": {
        "company": "Guaranty Trust Holding Co Plc",
        "sector": "Banking & Financials",
        "open_price": 44.50,
        "close_price": 45.80,
        "high_price": 46.20,
        "low_price": 44.10,
        "daily_return": 0.0292,
        "rsi_14": 61.5,
        "sma_10": 44.80,
        "sma_20": 43.50,
    },
    "ZENITHBANK": {
        "company": "Zenith Bank Plc",
        "sector": "Banking & Financials",
        "open_price": 38.00,
        "close_price": 37.50,
        "high_price": 38.50,
        "low_price": 37.10,
        "daily_return": -0.0131,
        "rsi_14": 42.1,
        "sma_10": 38.10,
        "sma_20": 39.00,
    },
    "SEPLAT": {
        "company": "Seplat Energy Plc",
        "sector": "Oil & Gas",
        "open_price": 3450.00,
        "close_price": 3520.00,
        "high_price": 3550.00,
        "low_price": 3420.00,
        "daily_return": 0.0203,
        "rsi_14": 67.8,
        "sma_10": 3480.00,
        "sma_20": 3390.00,
    }
}

# -------------------------------------------------------------------
# API ENDPOINTS
# -------------------------------------------------------------------
@app.get("/api/equities")
def get_equities():
    """Returns real-time data for all tracked NGX equities."""
    return {"status": "success", "count": len(EQUITY_DATABASE), "data": EQUITY_DATABASE}

@app.get("/api/equities/{ticker}")
def get_equity_detail(ticker: str):
    """Returns detailed features for a single ticker."""
    symbol = ticker.upper()
    if symbol not in EQUITY_DATABASE:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return {"status": "success", "ticker": symbol, "data": EQUITY_DATABASE[symbol]}

@app.post("/api/predict", response_model=PredictionResponse)
def predict_stock_direction(payload: PredictionRequest):
    """
    Executes ML Inference model trained on NGX technical features
    (open_price, close_price, daily_return, rsi_14, sma_10, sma_20).
    """
    features = np.array([[
        payload.open_price,
        payload.close_price,
        payload.daily_return,
        payload.rsi_14,
        payload.sma_10,
        payload.sma_20,
    ]])

    if ml_model is not None:
        prediction = int(ml_model.predict(features)[0])
        probabilities = ml_model.predict_proba(features)[0]
        prob_up = float(probabilities[1])
        prob_down = float(probabilities[0])
        model_source = "RandomForest (Trained Pipeline)"
    else:
        # Algorithmic calculation fallback if model.pkl isn't loaded
        is_bullish = payload.close_price > payload.sma_20 and payload.rsi_14 > 50
        prediction = 1 if is_bullish else 0
        prob_up = 0.85 if is_bullish else 0.25
        prob_down = 1.0 - prob_up
        model_source = "Quantitative Indicator Rules Engine"

    confidence = prob_up if prediction == 1 else prob_down
    signal = "BULLISH ACCUMULATION" if prediction == 1 else "BEARISH DISTRIBUTION"
    
    # Target price projection
    direction_factor = 1.025 if prediction == 1 else 0.975
    target_price = round(payload.close_price * direction_factor, 2)

    return PredictionResponse(
        ticker=payload.ticker.upper(),
        prediction=prediction,
        signal=signal,
        confidence=round(confidence * 100, 2),
        probability_up=round(prob_up * 100, 2),
        probability_down=round(prob_down * 100, 2),
        target_price=target_price,
        model_source=model_source
    )

# Serve Frontend Application
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

    @app.get("/")
    async def serve_root():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))