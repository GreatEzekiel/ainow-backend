from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from datetime import datetime, timezone
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class CompanyPrice(Base):
    __tablename__ = "company_prices"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    date = Column(DateTime, index=True, nullable=False)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float, default=0.0)
    daily_return = Column(Float, default=0.0)
    sma_10 = Column(Float, nullable=True)
    sma_20 = Column(Float, nullable=True)
    rsi_14 = Column(Float, nullable=True)

    __table_args__ = (UniqueConstraint("ticker", "date", name="uix_ticker_date"),)

class MarketIndex(Base):
    __tablename__ = "market_indices"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, unique=True, index=True, nullable=False)
    synthetic_ngx_asi = Column(Float, nullable=False)