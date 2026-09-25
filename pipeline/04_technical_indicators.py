"""
Step 4 – Technical Indicators.
Computes a comprehensive set of indicators using the `ta` library
and saves one CSV per ticker to data/features/.

Indicators computed:
  Trend   : SMA-20/50/200, EMA-12/26, MACD, ADX
  Momentum: RSI-14, Stochastic %K/%D, Williams %R, ROC-10
  Volatility: Bollinger Bands (20,2), ATR-14, Keltner Channels
  Volume  : OBV, VWAP (rolling approx.), CMF, MFI-14
"""

import os
import pandas as pd
import numpy as np
import ta

CLEANED_DIR  = os.path.join(os.path.dirname(__file__), "..", "data", "cleaned")
FEATURES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "features")
TICKERS      = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]


def load_cleaned(ticker: str) -> pd.DataFrame:
    fname = f"{ticker.replace('.', '_')}_cleaned.csv"
    return pd.read_csv(os.path.join(CLEANED_DIR, fname),
                       parse_dates=["Date"], index_col="Date")


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close  = df["Close"]
    high   = df["High"]
    low    = df["Low"]
    volume = df["Volume"]

    # ── Trend ────────────────────────────────────────────────────────────────
    df["SMA_20"]  = ta.trend.sma_indicator(close, window=20)
    df["SMA_50"]  = ta.trend.sma_indicator(close, window=50)
    df["SMA_200"] = ta.trend.sma_indicator(close, window=200)
    df["EMA_12"]  = ta.trend.ema_indicator(close, window=12)
    df["EMA_26"]  = ta.trend.ema_indicator(close, window=26)

    macd_obj      = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
    df["MACD"]         = macd_obj.macd()
    df["MACD_Signal"]  = macd_obj.macd_signal()
    df["MACD_Hist"]    = macd_obj.macd_diff()

    adx_obj       = ta.trend.ADXIndicator(high, low, close, window=14)
    df["ADX"]     = adx_obj.adx()
    df["DI_Plus"] = adx_obj.adx_pos()
    df["DI_Minus"]= adx_obj.adx_neg()

    df["Ichimoku_A"] = ta.trend.ichimoku_a(high, low)
    df["Ichimoku_B"] = ta.trend.ichimoku_b(high, low)

    # ── Momentum ─────────────────────────────────────────────────────────────
    df["RSI_14"]  = ta.momentum.rsi(close, window=14)

    stoch_obj     = ta.momentum.StochasticOscillator(high, low, close, window=14, smooth_window=3)
    df["Stoch_K"] = stoch_obj.stoch()
    df["Stoch_D"] = stoch_obj.stoch_signal()

    df["Williams_R"] = ta.momentum.williams_r(high, low, close, lbp=14)
    df["ROC_10"]     = ta.momentum.roc(close, window=10)
    df["TSI"]        = ta.momentum.tsi(close, window_slow=25, window_fast=13)

    # ── Volatility ────────────────────────────────────────────────────────────
    bb_obj           = ta.volatility.BollingerBands(close, window=20, window_dev=2)
    df["BB_Upper"]   = bb_obj.bollinger_hband()
    df["BB_Middle"]  = bb_obj.bollinger_mavg()
    df["BB_Lower"]   = bb_obj.bollinger_lband()
    df["BB_Width"]   = bb_obj.bollinger_wband()
    df["BB_Pct"]     = bb_obj.bollinger_pband()

    df["ATR_14"]     = ta.volatility.average_true_range(high, low, close, window=14)

    kc_obj           = ta.volatility.KeltnerChannel(high, low, close, window=20)
    df["KC_Upper"]   = kc_obj.keltner_channel_hband()
    df["KC_Lower"]   = kc_obj.keltner_channel_lband()

    # ── Volume ────────────────────────────────────────────────────────────────
    df["OBV"]        = ta.volume.on_balance_volume(close, volume)
    df["CMF"]        = ta.volume.chaikin_money_flow(high, low, close, volume, window=20)
    df["MFI_14"]     = ta.volume.money_flow_index(high, low, close, volume, window=14)
    df["EOM"]        = ta.volume.ease_of_movement(high, low, volume, window=14)

    # ── Derived features ──────────────────────────────────────────────────────
    df["Return_1d"]  = close.pct_change(1)
    df["Return_5d"]  = close.pct_change(5)
    df["Return_10d"] = close.pct_change(10)
    df["Return_20d"] = close.pct_change(20)

    df["Log_Return"] = np.log(close / close.shift(1))

    df["Price_SMA20_Ratio"] = close / df["SMA_20"]
    df["Price_SMA50_Ratio"] = close / df["SMA_50"]
    df["High_Low_Range"]    = (high - low) / close
    df["Close_Open_Range"]  = (close - df["Open"]) / df["Open"]

    # Rolling stats
    df["Vol_20d"]    = df["Return_1d"].rolling(20).std() * np.sqrt(252)
    df["Vol_60d"]    = df["Return_1d"].rolling(60).std() * np.sqrt(252)
    df["Skew_20d"]   = df["Return_1d"].rolling(20).skew()

    return df


def main():
    os.makedirs(FEATURES_DIR, exist_ok=True)
    for ticker in TICKERS:
        try:
            df = load_cleaned(ticker)
            df = add_indicators(df)
            out_path = os.path.join(FEATURES_DIR,
                                    f"{ticker.replace('.', '_')}_features.csv")
            df.to_csv(out_path)
            print(f"  [{ticker}] {len(df.columns)} columns, {len(df)} rows → {out_path}")
        except Exception as exc:
            print(f"  ERROR for {ticker}: {exc}")
    print("\nTechnical indicators computed for all tickers.")


if __name__ == "__main__":
    main()
