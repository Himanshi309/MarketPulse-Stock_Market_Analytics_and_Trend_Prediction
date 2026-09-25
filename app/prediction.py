"""
MarketPulse – Live Prediction
Loads the trained model artefact for a given ticker and returns
a BUY / HOLD-SELL signal based on the latest available feature row.
"""

import os
import joblib
import numpy as np
import pandas as pd

BASE_DIR     = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS_DIR   = os.path.join(BASE_DIR, "models")
FEATURES_DIR = os.path.join(BASE_DIR, "data", "features")

TICKERS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
THRESHOLD = 0.55


def load_artefact(ticker: str) -> dict:
    """Load model, scaler, and feature list for a ticker."""
    slug = ticker.replace(".", "_")
    path = os.path.join(MODELS_DIR, f"{slug}_model.pkl")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found: {path}")
    return joblib.load(path)


def get_latest_features(ticker: str, feature_cols: list) -> pd.DataFrame:
    """Return the most recent clean feature row from the ML dataset."""
    ml_path = os.path.join(FEATURES_DIR, "ml_dataset.csv")
    ml_df   = pd.read_csv(ml_path, parse_dates=["Date"], index_col="Date")
    feat_df = ml_df[ml_df["Ticker"] == ticker].sort_index()
    avail   = [c for c in feature_cols if c in feat_df.columns]
    row     = feat_df[avail].dropna().iloc[-1:]
    return row, avail


def predict(ticker: str) -> dict:
    """
    Run the trained model on the latest feature row.

    Returns a dict with:
        ticker, date, close, prob_up, signal, confidence
    """
    artefact = load_artefact(ticker)
    model, scaler, feature_cols = (
        artefact["model"],
        artefact["scaler"],
        artefact["features"],
    )

    row, avail = get_latest_features(ticker, feature_cols)
    if row.empty:
        raise ValueError(f"No clean feature row available for {ticker}")

    X        = scaler.transform(row[avail].values)
    prob_up  = float(model.predict_proba(X)[0, 1])
    pred_up  = int(prob_up >= THRESHOLD)

    # Latest close from raw features CSV
    slug     = ticker.replace(".", "_")
    raw_path = os.path.join(FEATURES_DIR, f"{slug}_features.csv")
    raw_df   = pd.read_csv(raw_path, parse_dates=["Date"], index_col="Date").sort_index()
    close    = float(raw_df["Close"].iloc[-1])

    return {
        "ticker":     ticker,
        "date":       str(row.index[-1].date()),
        "close":      round(close, 2),
        "prob_up":    round(prob_up, 4),
        "signal":     "BUY" if pred_up else "HOLD/SELL",
        "confidence": round(max(prob_up, 1 - prob_up) * 100, 1),
    }


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "RELIANCE.NS"
    result = predict(ticker)
    print(f"\nPrediction for {result['ticker']} ({result['date']})")
    print(f"  Signal     : {result['signal']}")
    print(f"  Prob UP    : {result['prob_up']:.4f}")
    print(f"  Confidence : {result['confidence']:.1f}%")
    print(f"  Close      : ₹{result['close']:,.2f}")
