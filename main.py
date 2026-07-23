import os
import numpy as np
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

import models, schemas, auth
from database import engine, Base, get_db
from websocket_manager import manager
from utils import load_artifact

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="NGX Alpha Labs API")

# Define frontend path
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

# Serve static directory if it exists
if os.path.exists(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

    @app.get("/")
    async def serve_root():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
    
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AINOW Quantitative API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load trained model artifact
MODEL_PATH = os.getenv("MODEL_PATH", "model.pkl")
ml_model = None
if os.path.exists(MODEL_PATH):
    try:
        ml_model = load_artifact(MODEL_PATH)
    except Exception:
        pass

# --- Authentication Routes ---
@app.post("/api/v1/auth/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=auth.get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/api/v1/auth/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not auth.verify_password(form_data.password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Public Endpoints ---
@app.get("/api/v1/metrics")
def get_metrics(db: Session = Depends(get_db)):
    total_records = db.query(models.CompanyPrice).count()
    distinct_tickers = db.query(models.CompanyPrice.ticker).distinct().count()
    return {
        "status": "online",
        "total_records": total_records,
        "active_tickers": distinct_tickers,
        "model_loaded": ml_model is not None,
    }

# --- Protected Data Routes ---
@app.get("/api/v1/tickers", response_model=List[schemas.TickerSummary])
def get_tickers(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    tickers = db.query(models.CompanyPrice.ticker).distinct().all()
    result = []
    for (t_name,) in tickers:
        latest = (
            db.query(models.CompanyPrice)
            .filter(models.CompanyPrice.ticker == t_name)
            .order_by(models.CompanyPrice.date.desc())
            .first()
        )
        if latest:
            pred = None
            if ml_model and latest.rsi_14 is not None and latest.sma_10 is not None and latest.sma_20 is not None:
                feats = np.array([[latest.open_price, latest.close_price, latest.daily_return, latest.rsi_14, latest.sma_10, latest.sma_20]])
                pred = int(ml_model.predict(feats)[0])
            result.append({
                "ticker": t_name,
                "last_price": latest.close_price,
                "daily_return": latest.daily_return,
                "rsi_14": latest.rsi_14,
                "prediction": pred,
            })
    return result

@app.get("/api/v1/chart/{ticker}", response_model=List[schemas.PricePoint])
def get_chart_data(
    ticker: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(models.CompanyPrice)
        .filter(models.CompanyPrice.ticker == ticker.upper())
        .order_by(models.CompanyPrice.date.asc())
        .all()
    )
    if not records:
        raise HTTPException(status_code=404, detail=f"No data found for ticker '{ticker}'")
    return records

@app.post("/api/v1/predict", response_model=schemas.PredictResponse)
def predict_direction(
    req: schemas.PredictRequest,
    current_user: models.User = Depends(auth.get_current_user),
):
    if not ml_model:
        raise HTTPException(status_code=503, detail="ML model is not loaded")
    
    feats = np.array([[req.open_price, req.close_price, req.daily_return, req.rsi_14, req.sma_10, req.sma_20]])
    pred = int(ml_model.predict(feats)[0])
    probs = ml_model.predict_proba(feats)[0]
    conf = float(probs[pred] * 100)

    return {
        "ticker": req.ticker,
        "prediction": pred,
        "label": "Likely Rise (1)" if pred == 1 else "Likely Fall (0)",
        "confidence": conf,
    }

# --- Real-Time WebSocket ---
@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)