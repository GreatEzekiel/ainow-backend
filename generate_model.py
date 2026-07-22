import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

def generate_placeholder_model():
    print("📦 Generating placeholder model.pkl...")

    # 1. Ensure output directories exist
    os.makedirs("models", exist_ok=True)
    os.makedirs("backend/app/models", exist_ok=True)  # Backup for nested app structure

    # 2. Generate dummy data with your 6 feature columns:
    # ["open_price", "close_price", "daily_return", "rsi_14", "sma_10", "sma_20"]
    X_dummy = np.random.rand(100, 6)
    y_dummy = np.random.randint(0, 2, size=100)

    # 3. Fit a lightweight model
    model = RandomForestClassifier(n_estimators=10, max_depth=3, random_state=42)
    model.fit(X_dummy, y_dummy)

    # 4. Save model.pkl to both likely folder paths
    path1 = "models/model.pkl"
    path2 = "backend/app/models/model.pkl"

    joblib.dump(model, path1)
    joblib.dump(model, path2)

    print(f"✅ Created: {os.path.abspath(path1)}")
    print(f"✅ Created: {os.path.abspath(path2)}")

if __name__ == "__main__":
    generate_placeholder_model()