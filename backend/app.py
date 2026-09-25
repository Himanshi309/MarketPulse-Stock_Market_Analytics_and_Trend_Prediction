"""
MarketPulse – Flask REST API Backend
Serves all data from the SQLite database to the frontend dashboard.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sqlalchemy import create_engine, text

BASE_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH   = os.path.join(BASE_DIR, "database", "marketpulse.db")
MODELS_DIR= os.path.join(BASE_DIR, "models")
STATIC_DIR= os.path.join(BASE_DIR, "frontend", "static")
FIGURES_DIR= os.path.join(BASE_DIR, "reports", "figures")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False,
                       connect_args={"check_same_thread": False})

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
CORS(app)

TICKERS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
SHORT_NAMES = {
    "RELIANCE.NS": "Reliance",
    "TCS.NS":      "TCS",
    "INFY.NS":     "Infosys",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS":"ICICI Bank",
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def query_db(sql: str, params: dict = None) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


def safe_json(df: pd.DataFrame) -> list:
    df = df.replace([np.inf, -np.inf], np.nan)
    return json.loads(df.to_json(orient="records", date_format="iso"))


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(os.path.join(BASE_DIR, "frontend"), "index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "db": os.path.exists(DB_PATH)})


@app.route("/api/tickers")
def get_tickers():
    return jsonify([{"ticker": t, "name": SHORT_NAMES[t]} for t in TICKERS])


@app.route("/api/prices")
def get_prices():
    ticker = request.args.get("ticker", "RELIANCE.NS")
    period = request.args.get("period", "2Y")   # 1Y | 2Y | 5Y | ALL
    period_map = {"1Y": 252, "2Y": 504, "5Y": 1260, "ALL": 99999}
    limit = period_map.get(period, 504)
    df = query_db(
        "SELECT date, open, high, low, close, volume "
        "FROM stock_prices WHERE ticker = :t ORDER BY date DESC LIMIT :n",
        {"t": ticker, "n": limit}
    )
    df = df.sort_values("date")
    return jsonify(safe_json(df))


@app.route("/api/indicators")
def get_indicators():
    ticker = request.args.get("ticker", "RELIANCE.NS")
    df = query_db(
        "SELECT date, sma_20, sma_50, sma_200, ema_12, ema_26, "
        "macd, macd_signal, macd_hist, rsi_14, stoch_k, stoch_d, adx, "
        "bb_upper, bb_lower, bb_pct, atr_14, mfi_14, vol_20d "
        "FROM technical_indicators WHERE ticker = :t ORDER BY date",
        {"t": ticker}
    )
    return jsonify(safe_json(df))


@app.route("/api/overview")
def get_overview():
    """Summary stats for all 5 tickers (latest price, change, volume)."""
    rows = []
    for ticker in TICKERS:
        df = query_db(
            "SELECT date, close, volume FROM stock_prices "
            "WHERE ticker = :t ORDER BY date DESC LIMIT 2",
            {"t": ticker}
        )
        if len(df) < 2:
            continue
        latest = df.iloc[0]
        prev   = df.iloc[1]
        chg_pct = (latest["close"] - prev["close"]) / prev["close"] * 100
        rows.append({
            "ticker":     ticker,
            "name":       SHORT_NAMES[ticker],
            "close":      round(float(latest["close"]), 2),
            "change_pct": round(float(chg_pct), 2),
            "volume":     int(latest["volume"]),
            "date":       str(latest["date"]),
        })
    return jsonify(rows)


@app.route("/api/predictions")
def get_predictions():
    ticker = request.args.get("ticker", "RELIANCE.NS")
    df = query_db(
        "SELECT date, close, predicted_up, prob_up, actual_target, correct "
        "FROM ml_predictions WHERE ticker = :t ORDER BY date",
        {"t": ticker}
    )
    return jsonify(safe_json(df))


@app.route("/api/backtest")
def get_backtest():
    df = query_db("SELECT * FROM backtest_results ORDER BY ticker")
    return jsonify(safe_json(df))


@app.route("/api/model_metrics")
def get_model_metrics():
    df = query_db("SELECT * FROM model_metrics ORDER BY ticker, roc_auc DESC")
    return jsonify(safe_json(df))


@app.route("/api/correlation")
def get_correlation():
    """Return daily close returns correlation matrix."""
    df = query_db(
        "SELECT date, ticker, close FROM stock_prices ORDER BY date"
    )
    pivot = df.pivot(index="date", columns="ticker", values="close")
    returns = pivot.pct_change().dropna()
    corr = returns.corr().round(4)
    result = {"tickers": list(corr.columns), "matrix": corr.values.tolist()}
    return jsonify(result)


@app.route("/api/predict", methods=["POST"])
def predict_live():
    """
    Accept the latest indicators for a ticker and return a model prediction.
    Body: { "ticker": "RELIANCE.NS" }
    Uses the latest row in the feature table.
    """
    data   = request.get_json(force=True)
    ticker = data.get("ticker", "RELIANCE.NS")
    ticker_slug = ticker.replace(".", "_")
    model_path  = os.path.join(MODELS_DIR, f"{ticker_slug}_model.pkl")
    if not os.path.exists(model_path):
        return jsonify({"error": "Model not found for this ticker"}), 404

    artefact = joblib.load(model_path)
    model, scaler, feature_cols = (artefact["model"],
                                   artefact["scaler"],
                                   artefact["features"])
    # Use ml_dataset.csv which has the same lag features as training
    ml_path = os.path.join(BASE_DIR, "data", "features", "ml_dataset.csv")
    ml_df = pd.read_csv(ml_path, parse_dates=["Date"], index_col="Date")
    feat_df = ml_df[ml_df["Ticker"] == ticker].sort_index()

    # Use raw features CSV for close price
    raw_feat_path = os.path.join(BASE_DIR, "data", "features",
                                 f"{ticker_slug}_features.csv")
    raw_feat = pd.read_csv(raw_feat_path, parse_dates=["Date"], index_col="Date").sort_index()

    avail_feats = [c for c in feature_cols if c in feat_df.columns]
    last_row = feat_df[avail_feats].dropna().iloc[-1:]
    if last_row.empty:
        return jsonify({"error": "No clean feature row available"}), 500

    X = scaler.transform(last_row[avail_feats].values)
    prob_up  = float(model.predict_proba(X)[0, 1])
    pred_up  = int(prob_up >= 0.55)
    last_close = float(raw_feat["Close"].iloc[-1])

    return jsonify({
        "ticker":     ticker,
        "name":       SHORT_NAMES.get(ticker, ticker),
        "date":       str(feat_df.index[-1].date()),
        "close":      round(last_close, 2),
        "prob_up":    round(prob_up, 4),
        "signal":     "BUY" if pred_up else "HOLD/SELL",
        "confidence": round(max(prob_up, 1-prob_up) * 100, 1),
    })


@app.route("/api/figures/<path:filename>")
def serve_figure(filename):
    return send_from_directory(FIGURES_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
