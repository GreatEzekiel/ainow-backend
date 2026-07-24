import pandas as pd
import importlib


def _import_setup_logger():
    """Try several possible module paths for setup_logger and return the callable."""
    candidates = [
        "utils",
        "training.utils",
        "backend.training.utils",
    ]
    for mod in candidates:
        try:
            module = importlib.import_module(mod)
            if hasattr(module, "setup_logger"):
                return getattr(module, "setup_logger")
        except ImportError:
            continue
    raise ImportError("Could not resolve import for setup_logger from any candidate module")

setup_logger = _import_setup_logger()

logger = setup_logger(__name__)

def clean_market_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip().lower() for col in df.columns]
    
    column_mapping = {
        "ticker_symbol": "ticker",
        "open": "open_price",
        "close": "close_price",
        "high": "high_price",
        "low": "low_price",
    }
    df.rename(columns=column_mapping, inplace=True)

    required_cols = ["ticker", "date", "open_price", "close_price", "high_price", "low_price"]
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"Missing required column in dataset: {col}")

    df["date"] = pd.to_datetime(df["date"])
    df.sort_values(by=["ticker", "date"], ascending=[True, True], inplace=True)
    df.drop_duplicates(subset=["ticker", "date"], keep="last", inplace=True)

    numeric_cols = ["open_price", "close_price", "high_price", "low_price"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df.dropna(subset=numeric_cols, inplace=True)
    df.reset_index(drop=True, inplace=True)
    logger.info(f"Cleaned dataset shape: {df.shape}")
    return df