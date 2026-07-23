import os
import sys
import pandas as pd
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
import models
from preprocess import clean_market_data
from feature_engineering import generate_features

def seed_database(reset: bool = False):
    print("🌱 Starting database seeding pipeline...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        if reset:
            print("⚠️ Reset flag detected: Clearing database tables...")
            db.query(models.CompanyPrice).delete()
            db.query(models.MarketIndex).delete()
            db.commit()

        data_file = "Data.xlsx"
        if not os.path.exists(data_file):
            raise FileNotFoundError(f"Data file '{data_file}' not found!")

        raw_df = pd.read_excel(data_file)
        cleaned = clean_market_data(raw_df)
        df = generate_features(cleaned)

        existing_pairs = set(db.query(models.CompanyPrice.ticker, models.CompanyPrice.date).all())
        records = []

        for _, row in df.iterrows():
            ticker = str(row["ticker"]).upper()
            dt = pd.to_datetime(row["date"]).to_pydatetime()

            if (ticker, dt) in existing_pairs:
                continue

            records.append(
                models.CompanyPrice(
                    ticker=ticker,
                    date=dt,
                    open_price=float(row["open_price"]),
                    high_price=float(row["high_price"]),
                    low_price=float(row["low_price"]),
                    close_price=float(row["close_price"]),
                    volume=float(row.get("volume", 0.0) or 0.0),
                    daily_return=float(row.get("daily_return", 0.0) or 0.0),
                    sma_10=float(row["sma_10"]) if pd.notnull(row.get("sma_10")) else None,
                    sma_20=float(row["sma_20"]) if pd.notnull(row.get("sma_20")) else None,
                    rsi_14=float(row["rsi_14"]) if pd.notnull(row.get("rsi_14")) else None,
                )
            )

        if records:
            db.bulk_save_objects(records)
            db.commit()
            print(f"✅ Inserted {len(records)} CompanyPrice records.")

        print("🎉 Seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"❌ Seeding error: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    reset_mode = "--reset" in sys.argv
    seed_database(reset=reset_mode)