import os
import sys
import numpy as np

try:
    from utils import setup_logger, load_artifact
except Exception:
    # Try dynamic import to avoid static import resolution errors in some IDEs
    try:
        import importlib

        mod = importlib.import_module("backend.training.utils")
        setup_logger = getattr(mod, "setup_logger")
        load_artifact = getattr(mod, "load_artifact")
    except Exception:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from utils import setup_logger, load_artifact

logger = setup_logger("predict_test")

MODEL_PATH = "model.pkl" if os.path.exists("model.pkl") else "../model.pkl"

SAMPLE_INPUT = {
    "ticker": "DANGCEM",
    "open_price": 280.00,
    "close_price": 285.50,
    "daily_return": 0.0196,
    "rsi_14": 58.4,
    "sma_10": 281.20,
    "sma_20": 278.00,
}


def test_inference():
    logger.info(f"Loading model from {MODEL_PATH}...")
    model = load_artifact(MODEL_PATH)

    features = np.array([[
        SAMPLE_INPUT["open_price"],
        SAMPLE_INPUT["close_price"],
        SAMPLE_INPUT["daily_return"],
        SAMPLE_INPUT["rsi_14"],
        SAMPLE_INPUT["sma_10"],
        SAMPLE_INPUT["sma_20"],
    ]])

    prediction = int(model.predict(features)[0])
    probabilities = model.predict_proba(features)[0]
    confidence = float(probabilities[prediction] * 100)

    label = "Likely Rise (1)" if prediction == 1 else "Likely Fall (0)"

    logger.info("--- Inference Test Results ---")
    logger.info(f"Ticker    : {SAMPLE_INPUT['ticker']}")
    logger.info(f"Prediction: {prediction} ({label})")
    logger.info(f"Confidence: {confidence:.2f}%")


if __name__ == "__main__":
    test_inference()