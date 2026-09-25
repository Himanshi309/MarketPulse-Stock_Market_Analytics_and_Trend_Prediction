"""
Step 5+6 – Create prediction targets and build the final ML feature matrix.

Targets:
  • Target_1d  – binary: 1 if Close[t+1] > Close[t] else 0
  • Target_5d  – binary: 1 if Close[t+5] > Close[t] else 0
  • Target_Return_1d – actual % return at t+1 (for regression)

Feature matrix:
  Lag features, technical indicators, and derived ratios are assembled into
  a single merged CSV (data/features/ml_dataset.csv) used by the model training step.
"""

import os
import pandas as pd
import numpy as np

FEATURES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "features")
TICKERS      = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]

FEATURE_COLS = [
    "Open", "High", "Low", "Close", "Volume",
    "SMA_20", "SMA_50", "SMA_200", "EMA_12", "EMA_26",
    "MACD", "MACD_Signal", "MACD_Hist",
    "ADX", "DI_Plus", "DI_Minus",
    "RSI_14", "Stoch_K", "Stoch_D", "Williams_R", "ROC_10", "TSI",
    "BB_Upper", "BB_Lower", "BB_Width", "BB_Pct",
    "ATR_14", "KC_Upper", "KC_Lower",
    "OBV", "CMF", "MFI_14",
    "Return_1d", "Return_5d", "Return_10d", "Return_20d", "Log_Return",
    "Price_SMA20_Ratio", "Price_SMA50_Ratio",
    "High_Low_Range", "Close_Open_Range",
    "Vol_20d", "Vol_60d", "Skew_20d",
]

LAG_COLS = ["RSI_14", "MACD", "Return_1d", "ATR_14", "Vol_20d",
            "BB_Pct", "MFI_14", "ADX"]
LAGS     = [1, 2, 3, 5]


def load_features(ticker: str) -> pd.DataFrame:
    fname = f"{ticker.replace('.', '_')}_features.csv"
    df    = pd.read_csv(os.path.join(FEATURES_DIR, fname),
                        parse_dates=["Date"], index_col="Date")
    return df


def build_targets(df: pd.DataFrame) -> pd.DataFrame:
    df["Target_1d"]         = (df["Close"].shift(-1) > df["Close"]).astype(int)
    df["Target_5d"]         = (df["Close"].shift(-5) > df["Close"]).astype(int)
    df["Target_Return_1d"]  = df["Close"].shift(-1) / df["Close"] - 1
    return df


def add_lags(df: pd.DataFrame) -> pd.DataFrame:
    for col in LAG_COLS:
        if col in df.columns:
            for lag in LAGS:
                df[f"{col}_lag{lag}"] = df[col].shift(lag)
    return df


def main():
    all_frames = []
    for ticker in TICKERS:
        try:
            df = load_features(ticker)
            df = build_targets(df)
            df = add_lags(df)
            df["Ticker"] = ticker

            # Keep only known feature cols + lag cols + target + ticker
            avail  = [c for c in FEATURE_COLS if c in df.columns]
            lag_cs = [c for c in df.columns if "_lag" in c]
            keep   = avail + lag_cs + ["Target_1d", "Target_5d",
                                        "Target_Return_1d", "Ticker"]
            df = df[keep]

            # Drop rows with NaN in any feature (warm-up period of indicators)
            feature_cols_all = avail + lag_cs
            df = df.dropna(subset=feature_cols_all)

            all_frames.append(df)
            print(f"  [{ticker}] {len(df)} rows, {len(df.columns)} columns")
        except Exception as exc:
            print(f"  ERROR for {ticker}: {exc}")

    ml_df = pd.concat(all_frames, axis=0)
    out_path = os.path.join(FEATURES_DIR, "ml_dataset.csv")
    ml_df.to_csv(out_path)
    print(f"\nML dataset: {len(ml_df)} rows × {len(ml_df.columns)} columns")
    print(f"Saved → {out_path}")

    # Per-ticker label balance check
    print("\nTarget_1d class balance:")
    bal = ml_df.groupby("Ticker")["Target_1d"].value_counts(normalize=True).unstack()
    print(bal.to_string())


if __name__ == "__main__":
    main()
