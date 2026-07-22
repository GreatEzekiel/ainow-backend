import numpy as np
from backend.training.utils import setup_logger, load_artifact

logger = setup_logger("predict_test")

MODEL_PATH = "../ngx_model.pkl"

# Feature order: ["open_price", "close_price", "daily_return", "rsi_14", "sma_10", "sma_20"]
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