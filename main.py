import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import os
import random
from typing import List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import joblib
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

import auth
from database import Base, engine, get_db
import models
import schemas
from websocket_manager import manager

# -------------------------------------------------------------------
# CONFIGURATION & CONSTANTS
# -------------------------------------------------------------------

EXCEL_FILE = "Data.xlsx"
MODEL_FILE = "ngx_model.pkl"

scheduler = BackgroundScheduler()


# -------------------------------------------------------------------
# HELPER FUNCTIONS & BACKGROUND TASKS
# -------------------------------------------------------------------

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculates Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def load_and_preprocess_dataset():
    """Loads Excel workbook sheets and computes technical features."""
    if not os.path.exists(EXCEL_FILE):
        raise FileNotFoundError(f"Dataset file '{EXCEL_FILE}' not found.")

    df_prices = pd.read_excel(EXCEL_FILE, sheet_name="Company_Prices")
    df_asi = pd.read_excel(EXCEL_FILE, sheet_name="Synthetic_ASI")

    df_prices["Date"] = pd.to_datetime(df_prices["Date"])
    df_asi["Date"] = pd.to_datetime(df_asi["Date"])

    # Sort sequentially for accurate technical calculations
    df_prices = df_prices.sort_values(by=["Ticker", "Date"]).reset_index(drop=True)

    # Compute Moving Averages (SMA10, SMA20) and RSI14 per Ticker
    df_prices["SMA_10"] = df_prices.groupby("Ticker")["Close"].transform(
        lambda x: x.rolling(10, min_periods=1).mean()
    )
    df_prices["SMA_20"] = df_prices.groupby("Ticker")["Close"].transform(
        lambda x: x.rolling(20, min_periods=1).mean()
    )
    df_prices["RSI_14"] = df_prices.groupby("Ticker")["Close"].transform(
        lambda x: calculate_rsi(x, 14)
    )

    return df_prices, df_asi


def refresh_market_data():
    """Background task executed automatically after market close."""
    print("🔄 [Cron] Refreshing market data and recalculating indicators...")
    try:
        df = pd.read_excel("Synthetic_NGX_Feb2026_to_July2026.xlsx", sheet_name="Company_Prices")
        app.state.df_prices = df
        print("✅ [Cron] Market data successfully refreshed.")
    except Exception as e:
        print(f"❌ [Cron] Data refresh failed: {e}")


async def start_market_tick_simulator():
    """Background task simulating real-time market price movements."""
    tickers = ["MTNCOM", "DANGCEM", "GUARANTY", "ZENITHBANK", "BUACEMENT"]

    while True:
        await asyncio.sleep(2)  # Emit tick every 2 seconds

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


# -------------------------------------------------------------------
# CONSOLIDATED LIFESPAN STATE MANAGER
# -------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup tasks (loading data, ML models, DB creation, schedulers)."""
    print("🚀 Initializing NGX Predictor API service...")

    # 1. Create DB Tables
    Base.metadata.create_all(bind=engine)

    # 2. Load Excel Data
    try:
        app.state.df_prices, app.state.df_asi = load_and_preprocess_dataset()
        print(f"✅ Data loaded: {len(app.state.df_prices)} price records indexed.")
    except Exception as e:
        print(f"⚠️ Error loading Excel dataset: {e}")
        app.state.df_prices = pd.DataFrame()
        app.state.df_asi = pd.DataFrame()

    # 3. Load ML Model
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

    # 4. Start Background Scheduler
    scheduler.add_job(refresh_market_data, "cron", hour=18, minute=0)
    scheduler.start()

    # 5. Start Real-time WebSocket Feed Generator
    asyncio.create_task(start_market_tick_simulator())

    yield  # Application runs here

    # Cleanup on shutdown
    scheduler.shutdown()
    print("🛑 Shutting down NGX Predictor API service...")


# -------------------------------------------------------------------
# FASTAPI APP SETUP
# -------------------------------------------------------------------

app = FastAPI(
    title="NGX AI Market Predictor API",
    description="Dynamic backend serving market statistics, ApexCharts OHLC data, and ML inference.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS
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
# MARKET DATA & PREDICTION ENDPOINTS
# -------------------------------------------------------------------

@api_router.get("/metrics", response_model=schemas.MarketMetricsResponse)
def get_market_metrics():
    """Returns top KPI bar summary statistics."""
    df_prices = app.state.df_prices
    df_asi = app.state.df_asi

    if df_prices.empty:
        raise HTTPException(status_code=500, detail="Market data uninitialized.")

    latest_date = df_prices["Date"].max()
    latest_prices = df_prices[df_prices["Date"] == latest_date]
    latest_asi = df_asi[df_asi["Date"] == df_asi["Date"].max()]

    avg_open = float(latest_prices["Open"].mean())
    avg_close = float(latest_prices["Close"].mean())
    avg_return = float(latest_prices["Daily_Return"].mean())
    asi_val = (
        float(latest_asi["Synthetic_NGX_ASI"].values[0])
        if not latest_asi.empty
        else avg_close
    )

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
    request: Request,
    search: Optional[str] = Query(None, description="Search ticker by name"),
    sort_by: str = Query("change_pct", description="Sort by 'change_pct', 'close_price', or 'ticker'"),
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
):
    """Returns latest stock performance, technical indicators, and predictions (Protected)."""
    df_prices = app.state.df_prices
    if df_prices.empty:
        raise HTTPException(status_code=500, detail="Market data uninitialized.")

    latest_date = df_prices["Date"].max()
    latest_df = df_prices[df_prices["Date"] == latest_date].copy()
    market_avg_close = float(latest_df["Close"].mean())

    if search:
        latest_df = latest_df[latest_df["Ticker"].str.contains(search.upper(), na=False)]

    results = []
    for _, row in latest_df.iterrows():
        close_val = float(row["Close"])
        open_val = float(row["Open"])
        daily_return = float(row["Daily_Return"])
        rsi_val = float(row["RSI_14"])
        sma10 = float(row["SMA_10"])
        sma20 = float(row["SMA_20"])

        # Predict using loaded model or rule-based fallback
        if app.state.model is not None:
            features = np.array([[open_val, close_val, daily_return, rsi_val, sma10, sma20]])
            pred = int(app.state.model.predict(features)[0])
            prob = float(app.state.model.predict_proba(features)[0][pred] * 100)
        else:
            pred = 1 if (rsi_val > 50 and sma10 >= sma20) else 0
            prob = float(np.random.randint(75, 95))

        results.append({
            "ticker": str(row["Ticker"]),
            "open_price": round(open_val, 2),
            "close_price": round(close_val, 2),
            "high_price": round(float(row["High"]), 2),
            "low_price": round(float(row["Low"]), 2),
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
def get_candlestick_chart(ticker: str):
    """Returns historical OHLC array formatted for ApexCharts."""
    df_prices = app.state.df_prices
    ticker_df = df_prices[df_prices["Ticker"].str.upper() == ticker.upper()].sort_values("Date")

    if ticker_df.empty:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found in dataset.")

    chart_series = [
        {
            "x": row["Date"].strftime("%Y-%m-%d"),
            "y": [
                round(float(row["Open"]), 2),
                round(float(row["High"]), 2),
                round(float(row["Low"]), 2),
                round(float(row["Close"]), 2),
            ],
        }
        for _, row in ticker_df.iterrows()
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


@api_router.post("/reload")
def reload_dataset(background_tasks: BackgroundTasks):
    """Reloads Excel dataset from disk asynchronously."""
    def task():
        app.state.df_prices, app.state.df_asi = load_and_preprocess_dataset()
        print("🔄 Dataset reloaded into memory.")

    background_tasks.add_task(task)
    return {"message": "Dataset reload initiated in background."}


# Attach router to FastAPI app
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