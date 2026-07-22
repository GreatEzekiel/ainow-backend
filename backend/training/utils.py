import os
import logging
import joblib
import pandas as pd


def setup_logger(name: str = "training_pipeline") -> logging.Logger:
    """Configures and returns a standard logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def load_raw_data(filepath: str) -> pd.DataFrame:
    """Loads raw Excel or CSV market data."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Source data file not found at: {filepath}")

    if filepath.endswith(".xlsx") or filepath.endswith(".xls"):
        return pd.read_excel(filepath)
    elif filepath.endswith(".csv"):
        return pd.read_csv(filepath)
    else:
        raise ValueError("Unsupported file format. Please provide .xlsx or .csv")


def save_artifact(obj, filepath: str) -> None:
    """Saves a trained model or artifact using joblib."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    joblib.dump(obj, filepath)


def load_artifact(filepath: str):
    """Loads a saved joblib artifact."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Artifact not found at: {filepath}")
    return joblib.load(filepath)