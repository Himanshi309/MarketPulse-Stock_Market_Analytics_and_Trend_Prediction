"""
Step 9 – SQL Database.

Creates a SQLite database (data/marketpulse.db) and populates it with:
  • stock_prices       – clean OHLCV per ticker per date
  • technical_indicators – all computed indicators
  • ml_predictions     – model predictions on the test set
  • backtest_results   – summary metrics per ticker
  • model_metrics      – CV model evaluation scores

All tables indexed on (ticker, date) for fast API queries.
"""

import os
import pandas as pd
import joblib
import numpy as np
import warnings
from sqlalchemy import create_engine, text

warnings.filterwarnings("ignore")

BASE_DIR     = os.path.join(os.path.dirname(__file__), "..")
CLEANED_DIR  = os.path.join(BASE_DIR, "data", "cleaned")
FEATURES_DIR = os.path.join(BASE_DIR, "data", "features")
MODELS_DIR   = os.path.join(BASE_DIR, "models")
REPORTS_DIR  = os.path.join(BASE_DIR, "reports")
DB_PATH      = os.path.join(BASE_DIR, "database", "marketpulse.db")
TICKERS      = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
TARGET       = "Target_1d"
THRESHOLD    = 0.55
TEST_FRAC    = 0.20
EXCLUDE_COLS = ["Target_1d", "Target_5d", "Target_Return_1d", "Ticker",
                "Open", "High", "Low", "Close", "Volume"]


def load_cleaned(ticker):
    fname = f"{ticker.replace('.', '_')}_cleaned.csv"
    df = pd.read_csv(os.path.join(CLEANED_DIR, fname),
                     parse_dates=["Date"], index_col="Date")
    df["ticker"] = ticker          # overwrite/set
    df = df.reset_index().rename(columns=str.lower)
    # drop duplicate 'ticker' columns if any
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def load_features(ticker):
    fname = f"{ticker.replace('.', '_')}_features.csv"
    df = pd.read_csv(os.path.join(FEATURES_DIR, fname),
                     parse_dates=["Date"], index_col="Date")
    df["ticker"] = ticker          # overwrite/set
    df = df.reset_index().rename(columns=str.lower)
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def get_predictions(ticker):
    ticker_slug = ticker.replace(".", "_")
    artefact_path = os.path.join(MODELS_DIR, f"{ticker_slug}_model.pkl")
    if not os.path.exists(artefact_path):
        return pd.DataFrame()

    artefact = joblib.load(artefact_path)
    model, scaler, feature_cols = artefact["model"], artefact["scaler"], artefact["features"]

    ml_df = pd.read_csv(os.path.join(FEATURES_DIR, "ml_dataset.csv"),
                        parse_dates=["Date"], index_col="Date")
    df = ml_df[ml_df["Ticker"] == ticker].sort_index()
    split = int(len(df) * (1 - TEST_FRAC))
    df_test = df.iloc[split:].copy()

    X_scaled = scaler.transform(df_test[feature_cols].values)
    probs    = model.predict_proba(X_scaled)[:, 1]
    preds    = (probs >= THRESHOLD).astype(int)
    actual   = df_test[TARGET].values

    feat_file = os.path.join(FEATURES_DIR, f"{ticker_slug}_features.csv")
    raw = pd.read_csv(feat_file, parse_dates=["Date"], index_col="Date")
    close = raw["Close"].loc[df_test.index]

    result = pd.DataFrame({
        "date":           df_test.index,
        "ticker":         ticker,
        "close":          close.values,
        "predicted_up":   preds,
        "prob_up":        np.round(probs, 4),
        "actual_target":  actual,
        "correct":        (preds == actual).astype(int),
    })
    return result


def main():
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

    # ── Table 1: stock_prices ──────────────────────────────────────────────────
    print("Loading stock prices …")
    prices = pd.concat([load_cleaned(t) for t in TICKERS])
    prices = prices[["date", "ticker", "open", "high", "low", "close", "volume"]]
    prices.to_sql("stock_prices", engine, if_exists="replace", index=False)
    print(f"  stock_prices: {len(prices)} rows")

    # ── Table 2: technical_indicators ─────────────────────────────────────────
    print("Loading technical indicators …")
    INDICATOR_COLS = [
        "date", "ticker",
        "sma_20", "sma_50", "sma_200", "ema_12", "ema_26",
        "macd", "macd_signal", "macd_hist",
        "rsi_14", "stoch_k", "stoch_d", "adx",
        "bb_upper", "bb_lower", "bb_width", "bb_pct",
        "atr_14", "obv", "cmf", "mfi_14",
        "return_1d", "return_5d", "vol_20d",
    ]
    feats = pd.concat([load_features(t) for t in TICKERS])
    # Keep only columns that exist
    keep_cols = [c for c in INDICATOR_COLS if c in feats.columns]
    feats = feats[keep_cols].dropna(subset=["rsi_14", "macd"])
    feats.to_sql("technical_indicators", engine, if_exists="replace", index=False)
    print(f"  technical_indicators: {len(feats)} rows")

    # ── Table 3: ml_predictions ────────────────────────────────────────────────
    print("Generating ML predictions …")
    preds_all = pd.concat([get_predictions(t) for t in TICKERS
                           if not get_predictions(t).empty])
    if not preds_all.empty:
        preds_all.to_sql("ml_predictions", engine, if_exists="replace", index=False)
        print(f"  ml_predictions: {len(preds_all)} rows")
    else:
        print("  ml_predictions: no data (run train step first)")

    # ── Table 4: backtest_results ──────────────────────────────────────────────
    bt_path = os.path.join(REPORTS_DIR, "backtest_results.csv")
    if os.path.exists(bt_path):
        bt = pd.read_csv(bt_path)
        bt.columns = [c.lower().replace(" ", "_") for c in bt.columns]
        bt.to_sql("backtest_results", engine, if_exists="replace", index=False)
        print(f"  backtest_results: {len(bt)} rows")

    # ── Table 5: model_metrics ─────────────────────────────────────────────────
    mm_path = os.path.join(REPORTS_DIR, "model_metrics.csv")
    if os.path.exists(mm_path):
        mm = pd.read_csv(mm_path)
        mm.columns = [c.lower() for c in mm.columns]
        mm.to_sql("model_metrics", engine, if_exists="replace", index=False)
        print(f"  model_metrics: {len(mm)} rows")

    # ── Create indexes ────────────────────────────────────────────────────────
    with engine.connect() as conn:
        for tbl in ["stock_prices", "technical_indicators", "ml_predictions"]:
            try:
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{tbl} "
                                  f"ON {tbl} (ticker, date)"))
            except Exception:
                pass
        conn.commit()

    print(f"\nDatabase ready: {DB_PATH}")

    # Quick validation
    with engine.connect() as conn:
        for tbl in ["stock_prices", "technical_indicators",
                    "ml_predictions", "backtest_results", "model_metrics"]:
            try:
                n = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
                print(f"  {tbl}: {n} rows")
            except Exception:
                print(f"  {tbl}: table missing")


if __name__ == "__main__":
    main()
