import os
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from backend.training.utils import setup_logger, load_raw_data, save_artifact
from backend.training.preprocess import clean_market_data
from backend.training.feature_engineering import generate_features
from backend.training.evaluate_model import evaluate_predictions

logger = setup_logger("train_model")

DATA_PATH = os.getenv("DATA_PATH", "../Data.xlsx")
MODEL_OUTPUT_PATH = os.getenv("MODEL_OUTPUT_PATH", "../ngx_model.pkl")

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