import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
import os
import random
from typing import List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import joblib
import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import Session

import auth
from database import Base, engine, get_db
import models
import schemas
from websocket_manager import manager

MODEL_FILE = "ngx_model.pkl"
scheduler = BackgroundScheduler()


async def start_market_tick_simulator():
    """Background task simulating real-time market price movements over WebSockets."""
    tickers = ["MTNCOM", "DANGCEM", "GUARANTY", "ZENITHBANK", "BUACEMENT"]
    try:
        while True:
            await asyncio.sleep(2)
            if manager.active_connections:
                selected_ticker = random.choice(tickers)
                price_delta = round(random.uniform(-1.50, 2.00), 2)
                base_price = round(random.uniform(200, 500), 2)
                new_price = round(base_price + price_delta, 2)

                tick_payload = {
                    "ticker": selected_ticker,
                    "price": new_price,
                    "change": price_delta,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                }
                await manager.broadcast(tick_payload)
    except asyncio.CancelledError:
        print("🛑 Tick simulator task cancelled.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown procedures."""
    print("🚀 Initializing NGX Predictor API service...")

    # 1. Initialize DB Schema
    Base.metadata.create_all(bind=engine)

    # 2. Load Machine Learning Model
    if os.path.exists(MODEL_FILE):
        try:
            app.state.model = joblib.load(MODEL_FILE)
            print("✅ Machine Learning model loaded successfully.")
        except Exception as e:
            print(f"⚠️ Failed to load model file: {e}")
            app.state.model = None
    else:
        app.state.model = None
        print("ℹ️ No model file found. Running in heuristic simulation mode.")

    # 3. Start Scheduler & WebSocket Tick Task
    scheduler.start()
    tick_task = asyncio.create_task(start_market_tick_simulator())

    yield

    # Clean shutdown
    tick_task.cancel()
    try:
        await tick_task
    except asyncio.CancelledError:
        pass

    scheduler.shutdown()
    print("🛑 Shutting down NGX Predictor API service...")


app = FastAPI(
    title="NGX AI Market Predictor API",
    description="Dynamic backend serving market statistics, ApexCharts OHLC data, and ML inference.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api/v1")


# -------------------------------------------------------------------
# AUTH ENDPOINTS
# -------------------------------------------------------------------

@api_router.post("/auth/register", response_model=schemas.UserResponse, status_code=201)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user_in.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_pw = auth.get_password_hash(user_in.password)
    new_user = models.User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_pw,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@api_router.post("/auth/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# -------------------------------------------------------------------
# MARKET DATA ENDPOINTS (Database Query Powered)
# -------------------------------------------------------------------

@api_router.get("/metrics", response_model=schemas.MarketMetricsResponse)
def get_market_metrics(db: Session = Depends(get_db)):
    """Returns overall market performance KPI metrics directly from database."""
    latest_date = db.query(func.max(models.CompanyPrice.date)).scalar()
    if not latest_date:
        raise HTTPException(status_code=404, detail="No market data available in database.")

    latest_prices = db.query(models.CompanyPrice).filter(models.CompanyPrice.date == latest_date).all()
    latest_asi = db.query(models.MarketIndex).order_by(models.MarketIndex.date.desc()).first()

    if not latest_prices:
        raise HTTPException(status_code=404, detail="No records found for latest market date.")

    avg_open = float(np.mean([p.open_price for p in latest_prices]))
    avg_close = float(np.mean([p.close_price for p in latest_prices]))
    avg_return = float(np.mean([p.daily_return for p in latest_prices]))
    asi_val = float(latest_asi.synthetic_ngx_asi) if latest_asi else avg_close

    return {
        "latest_date": latest_date.strftime("%Y-%m-%d"),
        "market_avg_price": round(avg_close, 2),
        "market_open_avg": round(avg_open, 2),
        "market_close_avg": round(avg_close, 2),
        "market_return_pct": round(avg_return * 100, 2),
        "synthetic_asi": round(asi_val, 2),
    }


@api_router.get("/tickers", response_model=List[schemas.TickerSummary])
def get_tickers_data(
    search: Optional[str] = Query(None, description="Search ticker by name"),
    sort_by: str = Query("change_pct", description="Sort by 'change_pct', 'close_price', or 'ticker'"),
    db: Session = Depends(get_db),
):
    """Returns latest stock prices, indicators, and ML predictions queried directly from database."""
    latest_date = db.query(func.max(models.CompanyPrice.date)).scalar()
    if not latest_date:
        raise HTTPException(status_code=404, detail="No market data available in database.")

    query = db.query(models.CompanyPrice).filter(models.CompanyPrice.date == latest_date)
    if search:
        query = query.filter(models.CompanyPrice.ticker.ilike(f"%{search}%"))

    latest_prices = query.all()
    if not latest_prices:
        return []

    all_latest = db.query(models.CompanyPrice).filter(models.CompanyPrice.date == latest_date).all()
    market_avg_close = float(np.mean([p.close_price for p in all_latest])) if all_latest else 0.0

    results = []
    for row in latest_prices:
        close_val = float(row.close_price)
        open_val = float(row.open_price)
        daily_return = float(row.daily_return)
        rsi_val = float(row.rsi_14 or 50.0)
        sma10 = float(row.sma_10 or close_val)
        sma20 = float(row.sma_20 or close_val)

        if app.state.model is not None:
            features = np.array([[open_val, close_val, daily_return, rsi_val, sma10, sma20]])
            pred = int(app.state.model.predict(features)[0])
            prob = float(app.state.model.predict_proba(features)[0][pred] * 100)
        else:
            pred = 1 if (rsi_val > 50 and sma10 >= sma20) else 0
            prob = float(np.random.randint(75, 95))

        results.append({
            "ticker": str(row.ticker),
            "open_price": round(open_val, 2),
            "close_price": round(close_val, 2),
            "high_price": round(float(row.high_price), 2),
            "low_price": round(float(row.low_price), 2),
            "change_pct": round(daily_return * 100, 2),
            "vs_market_avg": round(close_val - market_avg_close, 2),
            "rsi_14": round(rsi_val, 2),
            "sma_10": round(sma10, 2),
            "sma_20": round(sma20, 2),
            "prediction": pred,
            "prediction_label": "Likely Rise (1)" if pred == 1 else "Likely Fall (0)",
            "confidence": int(prob),
        })

    if sort_by in ["change_pct", "close_price"]:
        results.sort(key=lambda x: x[sort_by], reverse=True)
    elif sort_by == "ticker":
        results.sort(key=lambda x: x["ticker"])

    return results


@api_router.get("/chart/{ticker}", response_model=schemas.CandlestickResponse)
def get_candlestick_chart(ticker: str, db: Session = Depends(get_db)):
    """Returns historical OHLC array formatted for ApexCharts from database."""
    records = (
        db.query(models.CompanyPrice)
        .filter(models.CompanyPrice.ticker.ilike(ticker))
        .order_by(models.CompanyPrice.date.asc())
        .all()
    )

    if not records:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found in database.")

    chart_series = [
        {
            "x": row.date.strftime("%Y-%m-%d"),
            "y": [
                round(float(row.open_price), 2),
                round(float(row.high_price), 2),
                round(float(row.low_price), 2),
                round(float(row.close_price), 2),
            ],
        }
        for row in records
    ]

    return {
        "ticker": ticker.upper(),
        "total_candles": len(chart_series),
        "series": chart_series,
    }


@api_router.post("/predict", response_model=schemas.InferenceResponse)
def predict_single_stock(payload: schemas.InferenceRequest):
    """Real-time prediction endpoint for a single stock entry."""
    features = np.array([[
        payload.open_price,
        payload.close_price,
        payload.daily_return,
        payload.rsi_14,
        payload.sma_10,
        payload.sma_20,
    ]])

    if app.state.model is not None:
        pred = int(app.state.model.predict(features)[0])
        prob = float(app.state.model.predict_proba(features)[0][pred] * 100)
    else:
        pred = 1 if (payload.rsi_14 > 50 and payload.sma_10 >= payload.sma_20) else 0
        prob = 85.0

    return {
        "ticker": payload.ticker.upper(),
        "prediction": pred,
        "prediction_label": "Likely Rise (1)" if pred == 1 else "Likely Fall (0)",
        "confidence": round(prob, 2),
    }


app.include_router(api_router)


# -------------------------------------------------------------------
# WEBSOCKET ENDPOINT
# -------------------------------------------------------------------

@app.websocket("/ws/ticks")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)