from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CompanyPrice(Base):
    __tablename__ = "company_prices"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    date = Column(DateTime, index=True, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=True, default=0.0)
    daily_return = Column(Float, nullable=True, default=0.0)
    sma_10 = Column(Float, nullable=True)
    sma_20 = Column(Float, nullable=True)
    rsi_14 = Column(Float, nullable=True)

    __table_args__ = (
        Index("ix_ticker_date", "ticker", "date", unique=True),
    )


class MarketIndex(Base):
    __tablename__ = "market_index"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, unique=True, index=True, nullable=False)
    synthetic_ngx_asi = Column(Float, nullable=False)