import os
import sys
from pathlib import Path

# Add project root directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

import importlib.util
import pandas as pd
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
import models
from models import CompanyPrice, MarketIndex

config_path = BASE_DIR / "data" / "config.py"
spec = importlib.util.spec_from_file_location("data.config", str(config_path))
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load config module from '{config_path}'")
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)
CLEANED_CSV_PATH = config.CLEANED_CSV_PATH
FEATURE_CSV_PATH = config.FEATURE_CSV_PATH


def seed_database(reset: bool = False):
    """Populates PostgreSQL database from processed CSV data."""
    print("🌱 Starting database seeding pipeline...")

    # 1. Create database schema tables if they don't exist
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Optional: Clear tables if --reset flag is passed
        if reset:
            print("⚠️ Reset flag detected: Clearing existing table records...")
            db.query(CompanyPrice).delete()
            db.query(MarketIndex).delete()
            db.commit()

        # 2. Select data file from data/processed/
        data_file = FEATURE_CSV_PATH if FEATURE_CSV_PATH.exists() else CLEANED_CSV_PATH
        if not data_file.exists():
            raise FileNotFoundError(
                f"No processed dataset found at '{data_file}'. "
                "Please run 'python data/make_dataset.py' first!"
            )

        print(f"📖 Reading dataset from: {data_file}")
        df = pd.read_csv(data_file)
        df["date"] = pd.to_datetime(df["date"])

        # 3. Batch insert CompanyPrice records
        print("🚀 Bulk processing CompanyPrice records...")
        
        # Load existing (ticker, date) tuples to prevent primary key / unique constraint conflicts
        existing_pairs = set(
            db.query(CompanyPrice.ticker, CompanyPrice.date).all()
        )

        company_records = []
        for _, row in df.iterrows():
            ticker = str(row["ticker"]).upper()
            dt = row["date"].to_pydatetime()

            if (ticker, dt) in existing_pairs:
                continue  # Skip existing database rows

            record = CompanyPrice(
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
            company_records.append(record)

        if company_records:
            db.bulk_save_objects(company_records)
            db.commit()
            print(f"✅ Successfully inserted {len(company_records)} new CompanyPrice records.")
        else:
            print("ℹ️ All CompanyPrice records are already up to date.")

        # 4. Generate and seed MarketIndex synthetic benchmark records
        print("📈 Generating MarketIndex daily benchmark records...")
        daily_asi = (
            df.groupby("date")["close_price"]
            .mean()
            .reset_index()
            .rename(columns={"close_price": "synthetic_ngx_asi"})
        )

        existing_index_dates = set(r[0] for r in db.query(MarketIndex.date).all())
        asi_records = []

        for _, row in daily_asi.iterrows():
            dt = row["date"].to_pydatetime()
            if dt in existing_index_dates:
                continue

            asi_records.append(
                MarketIndex(
                    date=dt,
                    synthetic_ngx_asi=float(row["synthetic_ngx_asi"])
                )
            )

        if asi_records:
            db.bulk_save_objects(asi_records)
            db.commit()
            print(f"✅ Successfully inserted {len(asi_records)} new MarketIndex records.")
        else:
            print("ℹ️ MarketIndex records are already up to date.")

        print("🎉 Database seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed with error: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    reset_mode = "--reset" in sys.argv
    seed_database(reset=reset_mode)