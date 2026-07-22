import logging
import numpy as np
import pandas as pd

from backend.Data.config import (
    init_data_directories,
    RAW_EXCEL_PATH,
    EXTERNAL_INDEX_PATH,
    CLEANED_CSV_PATH,
    FEATURE_PARQUET_PATH,
    FEATURE_CSV_PATH,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("make_dataset")


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Computes Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()

    with np.errstate(divide="ignore", invalid="ignore"):
        rs = gain / loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        rsi = np.where(loss == 0, 100.0, rsi)

    return pd.Series(rsi, index=series.index).fillna(50.0)


def process_raw_to_cleaned() -> pd.DataFrame:
    """Loads raw Excel input and standardizes format into cleaned CSV."""
    if not RAW_EXCEL_PATH.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at '{RAW_EXCEL_PATH}'. "
            "Please place your 'Data.xlsx' file inside 'data/raw/'."
        )

    logger.info(f"Loading raw data from: {RAW_EXCEL_PATH}")
    df = pd.read_excel(RAW_EXCEL_PATH)

    # Standardize column headers
    df.columns = [str(col).strip().lower() for col in df.columns]

    column_mapping = {
        "ticker_symbol": "ticker",
        "open": "open_price",
        "close": "close_price",
        "high": "high_price",
        "low": "low_price",
    }
    df.rename(columns=column_mapping, inplace=True)

    # Convert dates & sort
    df["date"] = pd.to_datetime(df["date"])
    df.sort_values(by=["ticker", "date"], inplace=True)
    df.drop_duplicates(subset=["ticker", "date"], keep="last", inplace=True)

    # Coerce numeric values
    numeric_cols = ["open_price", "close_price", "high_price", "low_price"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df.dropna(subset=numeric_cols, inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Save cleaned intermediate file
    df.to_csv(CLEANED_CSV_PATH, index=False)
    logger.info(f"Cleaned dataset saved to: {CLEANED_CSV_PATH} ({len(df)} rows)")
    return df


def build_processed_features(cleaned_df: pd.DataFrame) -> pd.DataFrame:
    """Engineers technical indicators and integrates external index data."""
    df = cleaned_df.copy()

    # Calculate indicators per ticker group
    grouped = df.groupby("ticker", group_keys=False)
    df["daily_return"] = grouped["close_price"].pct_change().fillna(0.0)
    df["sma_10"] = grouped["close_price"].transform(lambda x: x.rolling(10, min_periods=1).mean())
    df["sma_20"] = grouped["close_price"].transform(lambda x: x.rolling(20, min_periods=1).mean())
    df["rsi_14"] = grouped["close_price"].transform(lambda x: calculate_rsi(x, 14))

    # Target variable (Next-day direction)
    df["target"] = grouped["close_price"].transform(lambda x: (x.shift(-1) > x).astype(int))

    # Merge external dataset if present
    if EXTERNAL_INDEX_PATH.exists():
        logger.info(f"Merging external index data from: {EXTERNAL_INDEX_PATH}")
        ext_df = pd.read_csv(EXTERNAL_INDEX_PATH)
        ext_df["date"] = pd.to_datetime(ext_df["date"])
        df = pd.merge(df, ext_df, on="date", how="left")
    else:
        logger.info("No external index dataset found in 'data/external/'. Skipping merge.")

    # Export finalized processed datasets
    df.to_parquet(FEATURE_PARQUET_PATH, index=False)
    df.to_csv(FEATURE_CSV_PATH, index=False)

    logger.info(f"Processed dataset saved to: {FEATURE_PARQUET_PATH} and {FEATURE_CSV_PATH}")
    return df


def run_data_pipeline():
    """Main execution function."""
    init_data_directories()
    cleaned_df = process_raw_to_cleaned()
    build_processed_features(cleaned_df)
    logger.info("Data pipeline execution complete!")


if __name__ == "__main__":
    run_data_pipeline()