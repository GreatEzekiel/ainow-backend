import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
import os
import random
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd

# Absolute path resolution ensures cloud environments find local assets regardless of working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = os.path.join(BASE_DIR, "Data.xlsx")
MODEL_FILE = os.path.join(BASE_DIR, "ngx_model.pkl")

# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

# --- Market Tick Simulator ---
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
        print("🛑 Market tick simulator task cancelled cleanly.")

# --- Lifespan Context Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start market simulation background task
    print("🚀 Starting application & background tasks...")
    simulator_task = asyncio.create_task(start_market_tick_simulator())
    yield
    # Shutdown: Cancel background task gracefully
    print("🛑 Shutting down application...")
    simulator_task.cancel()
    try:
        await simulator_task
    except asyncio.CancelledError:
        pass

# --- App Initialization ---
app = FastAPI(
    title="NGX Market Analytics API",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS (Required for external Streamlit frontends)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes & WebSockets ---
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "excel_found": os.path.exists(EXCEL_FILE),
        "model_found": os.path.exists(MODEL_FILE),
    }

@app.websocket("/ws/market-ticks")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keeps websocket connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)