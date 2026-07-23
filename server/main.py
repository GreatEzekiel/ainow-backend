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
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel


#app = FastAPI(
#    title="NGX Alpha Labs API Gateway",
#    version="2.1.0",
#    description="Institutional API for NGX Equities, ML Vector Signals, and Execution"
#)

app = FastAPI()

try:
    # Prefer local routers package if available
    from routers.equities import router as equities_router  # type: ignore[import]
except Exception:
    # Fallback: create an empty router placeholder so app can start without the package
    from fastapi import APIRouter
    equities_router = APIRouter()

# Make sure you include the router with the matching prefix
app.include_router(equities_router, prefix="/api/v1")

# ... [Your existing FastAPI routes (/api/login, /api/predict, etc.)] ...

# ==========================================
# STATIC FILE MOUNTING (SERVE FRONTEND & ADMIN)
# ==========================================

# 1. Mount the secret Admin Portal folder
if os.path.exists("admin-portal"):
    app.mount("/admin-portal", StaticFiles(directory="admin-portal", html=True), name="admin_portal")

# 2. Mount the main public frontend at root (Must be added LAST)
if os.path.exists("public"):
    app.mount("/", StaticFiles(directory="public", html=True), name="public_frontend")

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

@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "NGX Alpha Labs API",
        "docs": "/docs"
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


# --- Configuration ---
SECRET_KEY = "YOUR_SUPER_SECRET_KEY_CHANGE_IN_PRODUCTION"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize FastAPI App & Security Scheme
app = FastAPI(title="Institutional Quant Gateway", version="1.0.0")
security = HTTPBearer()

# --- Schemas ---
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- Security Helpers ---
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generates a signed JWT token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Extracts and verifies the Bearer token from the Authorization header."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- Endpoints ---

@app.get("/")
def health_check():
    """Root health check to prevent 404s on root hits."""
    return {"status": "online", "docs": "/docs"}

# Handlers for both /login and /api/login to match your gateway logs
@app.post("/login", response_model=TokenResponse, tags=["Auth"])
@app.post("/api/login", response_model=TokenResponse, tags=["Auth"])
def login(payload: LoginRequest):
    """Authenticate user and return JWT access token."""
    # Simple hardcoded check for testing (replace with database authentication)
    if payload.username == "admin" and payload.password == "secret123":
        access_token = create_access_token(data={"sub": payload.username})
        return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
    )

@app.get("/api/v1/equities", tags=["Equities"])
def get_equities(current_user: dict = Depends(verify_jwt_token)):
    """Protected endpoint requiring Authorization: Bearer <token>."""
    return {
        "status": "success",
        "user": current_user.get("sub"),
        "data": [
            {"symbol": "AAPL", "price": 185.20},
            {"symbol": "MSFT", "price": 420.50},
            {"symbol": "NVDA", "price": 120.30},
        ]
    }