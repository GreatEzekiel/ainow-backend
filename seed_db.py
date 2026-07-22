import os
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models

EXCEL_FILE = "Data.xlsx"

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)

def seed():
    print("📦 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    if not os.path.exists(EXCEL_FILE):
        print(f"❌ Dataset file '{EXCEL_FILE}' not found.")
        return

    print(f"📖 Reading {EXCEL_FILE}...")
    df_prices = pd.read_excel(EXCEL_FILE, sheet_name="Company_Prices")
    df_asi = pd.read_excel(EXCEL_FILE, sheet_name="Synthetic_ASI")

    df_prices["Date"] = pd.to_datetime(df_prices["Date"])
    df_asi["Date"] = pd.to_datetime(df_asi["Date"])

    df_prices = df_prices.sort_values(by=["Ticker", "Date"]).reset_index(drop=True)
    df_prices["Daily_Return"] = df_prices.groupby("Ticker")["Close"].pct_change().fillna(0.0)
    df_prices["SMA_10"] = df_prices.groupby("Ticker")["Close"].transform(lambda x: x.rolling(10, min_periods=1).mean())
    df_prices["SMA_20"] = df_prices.groupby("Ticker")["Close"].transform(lambda x: x.rolling(20, min_periods=1).mean())
    df_prices["RSI_14"] = df_prices.groupby("Ticker")["Close"].transform(lambda x: calculate_rsi(x, 14))

    if db.query(models.CompanyPrice).first() is None:
        print("⏳ Seeding company price records...")
        price_records = [
            models.CompanyPrice(
                ticker=str(row["Ticker"]),
                date=row["Date"],
                open_price=float(row["Open"]),
                high_price=float(row["High"]),
                low_price=float(row["Low"]),
                close_price=float(row["Close"]),
                volume=float(row.get("Volume", 0.0)) if not pd.isna(row.get("Volume", 0.0)) else 0.0,
                daily_return=float(row["Daily_Return"]),
                sma_10=float(row["SMA_10"]),
                sma_20=float(row["SMA_20"]),
                rsi_14=float(row["RSI_14"]),
            )
            for _, row in df_prices.iterrows()
        ]
        db.bulk_save_objects(price_records)
        db.commit()
        print(f"✅ Seeded {len(price_records)} price records.")
    else:
        print("ℹ️ Company prices table already populated. Skipping.")

    if db.query(models.MarketIndex).first() is None:
        print("⏳ Seeding ASI Market Index records...")
        asi_records = [
            models.MarketIndex(
                date=row["Date"],
                synthetic_ngx_asi=float(row["Synthetic_NGX_ASI"]),
            )
            for _, row in df_asi.iterrows()
        ]
        db.bulk_save_objects(asi_records)
        db.commit()
        print(f"✅ Seeded {len(asi_records)} ASI records.")
    else:
        print("ℹ️ Market index table already populated. Skipping.")

    db.close()
    print("🚀 Database seeding process completed successfully!")

if __name__ == "__main__":
    seed()