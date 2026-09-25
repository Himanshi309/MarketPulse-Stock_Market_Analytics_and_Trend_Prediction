"""
Step 2 – Clean raw OHLCV data.
• Drops duplicates & all-NaN rows
• Forward-fills single-day gaps (exchange holidays)
• Validates OHLC relationships
• Saves cleaned CSVs to data/cleaned/
"""

import os
import pandas as pd
import numpy as np

RAW_DIR     = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
CLEANED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cleaned")
TICKERS     = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]


def load_raw(ticker: str) -> pd.DataFrame:
    fname = f"{ticker.replace('.', '_')}.csv"
    path  = os.path.join(RAW_DIR, fname)
    df    = pd.read_csv(path, parse_dates=["Date"], index_col="Date")
    return df


def clean(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    original_len = len(df)

    # ── 1. Sort chronologically ──────────────────────────────────────────────
    df = df.sort_index()

    # ── 2. Drop duplicate index entries ─────────────────────────────────────
    df = df[~df.index.duplicated(keep="first")]

    # ── 3. Drop rows where all OHLCV are NaN ────────────────────────────────
    ohlcv_cols = ["Open", "High", "Low", "Close", "Volume"]
    df = df.dropna(subset=ohlcv_cols, how="all")

    # ── 4. Forward-fill up to 3 consecutive missing days (holidays) ──────────
    df[ohlcv_cols] = df[ohlcv_cols].ffill(limit=3)

    # ── 5. Drop any remaining rows with NaN in price columns ────────────────
    df = df.dropna(subset=["Open", "High", "Low", "Close"])

    # ── 6. Replace zero volume with NaN then forward-fill ───────────────────
    df["Volume"] = df["Volume"].replace(0, np.nan).ffill()

    # ── 7. OHLC sanity check ─────────────────────────────────────────────────
    bad_rows = df[(df["High"] < df["Low"]) |
                  (df["High"] < df["Close"]) |
                  (df["Low"]  > df["Close"])]
    if not bad_rows.empty:
        print(f"  [{ticker}] Dropping {len(bad_rows)} OHLC-inconsistent rows")
        df = df.drop(bad_rows.index)

    # ── 8. Remove extreme outliers (price change > 50 % in one day) ──────────
    daily_ret = df["Close"].pct_change().abs()
    outliers  = daily_ret[daily_ret > 0.50].index
    if len(outliers):
        print(f"  [{ticker}] Dropping {len(outliers)} price-spike outliers")
        df = df.drop(outliers)

    # ── 9. Ensure numeric dtypes ─────────────────────────────────────────────
    for col in ohlcv_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=ohlcv_cols)

    # ── 10. Reset ticker column ──────────────────────────────────────────────
    df["Ticker"] = ticker

    print(f"  [{ticker}] {original_len} → {len(df)} rows after cleaning")
    return df


def main():
    os.makedirs(CLEANED_DIR, exist_ok=True)
    report_rows = []
    for ticker in TICKERS:
        try:
            raw = load_raw(ticker)
            cleaned = clean(raw, ticker)
            out_path = os.path.join(CLEANED_DIR, f"{ticker.replace('.', '_')}_cleaned.csv")
            cleaned.to_csv(out_path)
            report_rows.append({
                "Ticker":       ticker,
                "Clean_Rows":   len(cleaned),
                "Date_Start":   str(cleaned.index.min().date()),
                "Date_End":     str(cleaned.index.max().date()),
                "Missing_Close": int(cleaned["Close"].isna().sum()),
            })
        except FileNotFoundError:
            print(f"  Raw file not found for {ticker} – run 01_download_data.py first")

    report = pd.DataFrame(report_rows)
    report_path = os.path.join(CLEANED_DIR, "cleaning_report.csv")
    report.to_csv(report_path, index=False)
    print(f"\nCleaning complete.\n{report.to_string(index=False)}")


if __name__ == "__main__":
    main()
