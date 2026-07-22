import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

EXCEL_FILE = "Data.xlsx"
MODEL_OUTPUT = "ngx_model.pkl"

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50.0)

def train_and_export_model():
    print("📥 Loading Excel dataset...")
    df = pd.read_excel(EXCEL_FILE, sheet_name='Company_Prices')
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by=['Ticker', 'Date']).reset_index(drop=True)

    # Technical Feature Engineering
    print("⚙️ Computing technical features...")
    df['SMA_10'] = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(10, min_periods=1).mean())
    df['SMA_20'] = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(20, min_periods=1).mean())
    df['RSI_14'] = df.groupby('Ticker')['Close'].transform(lambda x: calculate_rsi(x, 14))

    # Binary Target: 1 if Next Day Return >= 0, else 0
    df['Next_Close'] = df.groupby('Ticker')['Close'].shift(-1)
    df['Target'] = (df['Next_Close'] >= df['Close']).astype(int)

    # Drop NaNs created by shift
    df = df.dropna().reset_index(drop=True)

    features = ['Open', 'Close', 'Daily_Return', 'RSI_14', 'SMA_10', 'SMA_20']
    X = df[features]
    y = df['Target']

    # Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print("🤖 Training Random Forest Model...")
    model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    model.fit(X_train, y_train)

    # Evaluation
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"✅ Training completed. Test Accuracy: {acc * 100:.2f}%")
    print("\nClassification Report:\n", classification_report(y_test, preds))

    # Save to disk
    joblib.dump(model, MODEL_OUTPUT)
    print(f"📦 Model successfully exported to '{MODEL_OUTPUT}'.")

if __name__ == "__main__":
    train_and_export_model()