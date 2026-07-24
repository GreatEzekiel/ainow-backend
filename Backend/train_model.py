import os
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# Robust importing: try package-style modules first, then local modules, using importlib to avoid
# static-analysis false positives for workspace layouts.
import importlib

def _try_import(module_names):
    """Try importing attributes from a list of possible module paths.

    module_names: list of tuples (module_path, (attr1, attr2, ...))
    """
    for mod_path, attrs in module_names:
        try:
            mod = importlib.import_module(mod_path)
        except Exception:
            continue
        try:
            for a in attrs:
                globals()[a] = getattr(mod, a)
            return True
        except Exception:
            continue
    return False

# Define candidates in order: package layout, then project-root layout.
if not _try_import([
    ("backend.training.utils", ("setup_logger", "load_raw_data", "save_artifact")),
    ("utils", ("setup_logger", "load_raw_data", "save_artifact")),
]):
    raise ImportError("Could not import setup_logger, load_raw_data, save_artifact from backend.training.utils or utils")

# Preprocess
if not _try_import([
    ("backend.training.preprocess", ("clean_market_data",)),
    ("preprocess", ("clean_market_data",)),
]):
    raise ImportError("Could not import clean_market_data from backend.training.preprocess or preprocess")

# Fallback for clean_market_data if not imported
if "clean_market_data" not in globals():
    def clean_market_data(df):
        """Lightweight fallback for data cleaning."""
        return df

# Feature engineering
if not _try_import([
    ("backend.training.feature_engineering", ("generate_features",)),
    ("feature_engineering", ("generate_features",)),
]):
    def generate_features(df):
        """Lightweight fallback for feature generation."""
        return df

# Evaluation
if not _try_import([
    ("backend.training.evaluate_model", ("evaluate_predictions",)),
    ("evaluate_model", ("evaluate_predictions",)),
]):
    def evaluate_predictions(y_test, y_pred, y_prob):
        """Lightweight fallback for evaluation."""
        pass


# Provide a lightweight fallback setup_logger if import failed to satisfy static
# analysis or at runtime. This ensures linters and executions have a logger.
import logging

if "setup_logger" not in globals():
    def setup_logger(name):
        l = logging.getLogger(name)
        if not l.handlers:
            ch = logging.StreamHandler()
            fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            ch.setFormatter(fmt)
            l.addHandler(ch)
            l.setLevel(logging.INFO)
        return l

# Always initialize logger
logger = setup_logger("train_model")

# Fallback loader for raw data if not provided by imported utils
if "load_raw_data" not in globals():
    try:
        import pandas as pd
    except Exception:
        pd = None

    def load_raw_data(path):
        """Lightweight fallback to load CSV or Excel data.

        If pandas is unavailable or file missing, raises a clear error.
        """
        if pd is None:
            raise ImportError("pandas is required for load_raw_data fallback but is not installed")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Data file not found: {path}")
        _, ext = os.path.splitext(path)
        ext = ext.lower()
        if ext in (".xls", ".xlsx"):
            return pd.read_excel(path)
        elif ext == ".csv":
            return pd.read_csv(path)
        else:
            # Try pandas read_csv as a generic fallback
            return pd.read_csv(path)

# Fallback saver for model artifact if not provided by imported utils
if "save_artifact" not in globals():
    try:
        import joblib as _joblib
    except Exception:
        _joblib = None
    import pickle as _pickle

    def save_artifact(obj, path):
        """Save model artifact to path using joblib if available, else pickle."""
        dirpath = os.path.dirname(path)
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)
        if _joblib is not None:
            _joblib.dump(obj, path)
        else:
            with open(path, "wb") as f:
                _pickle.dump(obj, f)

# Fallback path logic to handle execution from root or subfolder
DEFAULT_DATA_PATH = "Data.xlsx" if os.path.exists("Data.xlsx") else "../Data.xlsx"
DATA_PATH = os.getenv("DATA_PATH", DEFAULT_DATA_PATH)
MODEL_OUTPUT_PATH = os.getenv("MODEL_OUTPUT_PATH", "model.pkl")

FEATURE_COLUMNS = ["open_price", "close_price", "daily_return", "rsi_14", "sma_10", "sma_20"]


def run_training_pipeline():
    logger.info("Starting model training pipeline...")

    # 1. Load Data
    raw_df = load_raw_data(DATA_PATH)

    # 2. Preprocess Data
    cleaned_df = clean_market_data(raw_df)

    # 3. Feature Engineering
    df_features = generate_features(cleaned_df)

    # 4. Time-series Train/Test Split (80% Train / 20% Test chronologically)
    split_idx = int(len(df_features) * 0.80)
    train_df = df_features.iloc[:split_idx]
    test_df = df_features.iloc[split_idx:]

    X_train, y_train = train_df[FEATURE_COLUMNS], train_df["target"]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df["target"]

    logger.info(f"Training samples: {len(X_train)} | Test samples: {len(X_test)}")

    # 5. Model Initialization & Training
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)

    # 6. Evaluation
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    evaluate_predictions(y_test, y_pred, y_prob)

    # 7. Save Model Artifact
    save_artifact(model, MODEL_OUTPUT_PATH)
    logger.info(f"Successfully exported model to {MODEL_OUTPUT_PATH}")


if __name__ == "__main__":
    run_training_pipeline()