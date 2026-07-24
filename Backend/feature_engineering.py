import numpy as np
import pandas as pd
import importlib

# Try to import setup_logger from the project package; fall back to local utils
try:
    _utils = importlib.import_module("backend.training.utils")
    setup_logger = getattr(_utils, "setup_logger")
except Exception:
    from utils import setup_logger

logger = setup_logger(__name__)


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculates Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()

    with np.errstate(divide="ignore", invalid="ignore"):
        rs = gain / loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        rsi = np.where(loss == 0, 100.0, rsi)

    return pd.Series(rsi, index=series.index).fillna(50.0)


def generate_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineers price indicators per ticker group."""
    df = df.copy()

    # Calculate indicators per ticker group to avoid cross-ticker leakage
    grouped = df.groupby("ticker", group_keys=False)

    df["daily_return"] = grouped["close_price"].pct_change().fillna(0.0)
    df["sma_10"] = grouped["close_price"].transform(lambda x: x.rolling(10, min_periods=1).mean())
    df["sma_20"] = grouped["close_price"].transform(lambda x: x.rolling(20, min_periods=1).mean())
    df["rsi_14"] = grouped["close_price"].transform(lambda x: calculate_rsi(x, 14))

    # Binary Target: 1 if next day's close price is higher than current close, else 0
    df["target"] = grouped["close_price"].transform(lambda x: (x.shift(-1) > x).astype(int))

    # Drop the final row per ticker group without losing the 'ticker' column
    last_indices = df.groupby("ticker").tail(1).index
    df = df.drop(index=last_indices).reset_index(drop=True)

    logger.info("Features engineered successfully: ['daily_return', 'rsi_14', 'sma_10', 'sma_20']")
    return df