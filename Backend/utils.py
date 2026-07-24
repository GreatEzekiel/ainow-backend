import os
import logging
import joblib
import pandas as pd

def setup_logger(name: str = "training_pipeline") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_raw_data(filepath: str) -> pd.DataFrame:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Source data file not found at: {filepath}")
    if filepath.endswith((".xlsx", ".xls")):
        return pd.read_excel(filepath)
    elif filepath.endswith(".csv"):
        return pd.read_csv(filepath)
    raise ValueError("Unsupported file format. Provide .xlsx or .csv")

def save_artifact(obj, filepath: str) -> None:
    dirname = os.path.dirname(filepath)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    joblib.dump(obj, filepath)

def load_artifact(filepath: str):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Artifact not found at: {filepath}")
    return joblib.load(filepath)