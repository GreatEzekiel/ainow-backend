import pandas as pd
from backend.training.utils import setup_logger

logger = setup_logger(__name__)


def clean_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans raw market price DataFrame and standardizes column formats."""
    df = df.copy()

    # Standardize column headers to lowercase
    df.columns = [str(col).strip().lower() for col in df.columns]

    # Map legacy column names if present
    column_mapping = {
        "ticker_symbol": "ticker",
        "open": "open_price",
        "close": "close_price",
        "high": "high_price",
        "low": "low_price",
    }
    df.rename(columns=column_mapping, inplace=True)

    # Validate essential columns
    required_cols = ["ticker", "date", "open_price", "close_price", "high_price", "low_price"]
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"Missing required column in dataset: {col}")

    # Convert dates & sort chronologically per ticker
    df["date"] = pd.to_datetime(df["date"])
    df.sort_values(by=["ticker", "date"], ascending=[True, True], inplace=True)
    df.drop_duplicates(subset=["ticker", "date"], keep="last", inplace=True)

    # Coerce numeric price columns
    numeric_cols = ["open_price", "close_price", "high_price", "low_price"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop missing initial rows
    df.dropna(subset=numeric_cols, inplace=True)
    df.reset_index(drop=True, inplace=True)

    logger.info(f"Cleaned dataset shape: {df.shape}")
    return df