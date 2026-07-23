"""
NGX Alpha Labs - Quantitative Backend & ML Prediction Engine
Framework: FastAPI + Pydantic
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import datetime
import random
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(
    title="NGX Alpha Labs API Gateway",
    version="2.1.0",
    description="Institutional API for NGX Equities, ML Vector Signals, and Execution"
)

# Mount the 'public' folder so FastAPI serves index.html at the root URL
if os.path.exists("public"):
    app.mount("/", StaticFiles(directory="public", html=True), name="static")

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# IN-MEMORY STORAGE & SCHEMAS
# ==========================================

# Mock User DB
USER_DB: Dict[str, Dict[str, Any]] = {
    "seun@firm.com": {
        "full_name": "Luky Seun",
        "email": "seun@firm.com",
        "password_hash": "hashed_secret_pass",
        "role": "Senior Equity Strategist"
    }
}

class UserSignUp(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PredictRequest(BaseModel):
    symbol: str
    timeframe: Optional[str] = "1D"

class OrderRequest(BaseModel):
    symbol: str
    action: str  # BUY or SELL
    quantity: int
    price: float

# ==========================================
# AUTHENTICATION ENDPOINTS
# ==========================================

@app.post("/api/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserSignUp):
    if user.email in USER_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this institutional email already exists."
        )
    
    USER_DB[user.email] = {
        "full_name": user.full_name,
        "email": user.email,
        "password_hash": f"hashed_{user.password}",
        "role": "Registered Quant Member"
    }

    return {
        "status": "success",
        "message": "User registered successfully.",
        "user": {
            "name": user.full_name,
            "email": user.email,
            "role": "Registered Quant Member"
        },
        "token": f"jwt_token_{random.randint(100000, 999999)}"
    }

@app.post("/api/login")
async def login(credentials: UserLogin):
    user = USER_DB.get(credentials.email)
    # If user does not exist, create a demo fallback user
    if user is None:
        USER_DB[credentials.email] = {
            "full_name": credentials.email.split("@")[0].upper(),
            "email": credentials.email,
            "role": "Quant Analyst"
        }
        user = USER_DB[credentials.email]
    else:
        # If user exists but password does not match, reject authentication
        if user.get("password_hash") != f"hashed_{credentials.password}":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

    return {
        "status": "success",
        "message": "Authentication successful.",
        "user": {
            "name": user["full_name"],
            "email": user["email"],
            "role": user.get("role", "Quant Analyst")
        },
        "token": f"jwt_token_{random.randint(100000, 999999)}"
    }

# ==========================================
# QUANTITATIVE & ML ENDPOINTS
# ==========================================

@app.post("/api/predict")
async def get_ml_prediction(request: PredictRequest):
    symbol = request.symbol.upper()
    
    tickers_db = {
        "MTNN": {
            "symbol": "MTNN",
            "company": "MTN Nigeria Communications Plc",
            "sector": "Telecommunications",
            "signal": "BULLISH ACCUMULATION",
            "confidence": 87.4,
            "target_price": 255.00,
            "current_price": 235.00
        },
        "DANGCEM": {
            "symbol": "DANGCEM",
            "company": "Dangote Cement Plc",
            "sector": "Industrial Goods",
            "signal": "STRONG BUY",
            "confidence": 92.1,
            "target_price": 710.00,
            "current_price": 655.00
        }
    }

    data = tickers_db.get(symbol, {
        "symbol": symbol,
        "company": f"{symbol} Nigeria Plc",
        "sector": "NGX Main Board",
        "signal": "NEUTRAL HOLD",
        "confidence": 65.0,
        "target_price": 100.00,
        "current_price": 95.00
    })

    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "model_version": "XGBoost-Vector-v4.2",
        "prediction": data
    }

@app.get("/api/market-summary")
async def get_market_summary():
    return {
        "asi": 104210.45,
        "asi_change_pct": 0.84,
        "market_cap_naira_trillion": 58.92,
        "daily_turnover_naira_billion": 14.25,
        "volume_traded_million": 485.2,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@app.post("/api/order")
async def execute_order(order: OrderRequest):
    return {
        "order_id": f"ORD-NGX-{random.randint(100000, 999999)}",
        "symbol": order.symbol,
        "action": order.action,
        "executed_price": order.price,
        "quantity": order.quantity,
        "status": "FILLED",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)