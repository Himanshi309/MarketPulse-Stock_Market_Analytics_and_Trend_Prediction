"""
Step 1 – Download historical OHLCV data for NSE-listed stocks via yfinance.
Saves one CSV per ticker into data/raw/.
"""

import os
import time
import yfinance as yf
import pandas as pd

TICKERS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
START_DATE = "2018-01-01"
END_DATE   = "2024-12-31"
RAW_DIR    = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def download_ticker(ticker: str) -> pd.DataFrame:
    print(f"  Downloading {ticker} …")
    df = yf.download(
        ticker,
        start=START_DATE,
        end=END_DATE,
        auto_adjust=True,
        progress=False,
    )
    if df.empty:
        raise ValueError(f"No data returned for {ticker}")
    df.index.name = "Date"
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    df = df[["Open", "High", "Low", "Close", "Volume"]]
    df["Ticker"] = ticker
    return df


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    summary = []
    for ticker in TICKERS:
        try:
            df = download_ticker(ticker)
            out_path = os.path.join(RAW_DIR, f"{ticker.replace('.', '_')}.csv")
            df.to_csv(out_path)
            summary.append({
                "Ticker": ticker,
                "Rows": len(df),
                "Start": str(df.index.min().date()),
                "End":   str(df.index.max().date()),
                "File":  out_path,
            })
            print(f"    Saved {len(df)} rows → {out_path}")
        except Exception as exc:
            print(f"  ERROR for {ticker}: {exc}")
        time.sleep(1)          # be polite to the API

    summary_df = pd.DataFrame(summary)
    summary_path = os.path.join(RAW_DIR, "download_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"\nDownload complete. Summary saved to {summary_path}")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
