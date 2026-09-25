"""
MarketPulse – Portfolio Analytics
Tracks a user-defined portfolio of NSE stocks, computes weights,
P&L, and risk metrics using data from the SQLite database.
"""

import os
import sqlite3
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH  = os.path.join(BASE_DIR, "database", "marketpulse.db")

DEFAULT_PORTFOLIO = {
    "RELIANCE.NS":  20,
    "TCS.NS":       20,
    "INFY.NS":      20,
    "HDFCBANK.NS":  20,
    "ICICIBANK.NS": 20,
}


def load_prices(tickers: list, period_days: int = 252) -> pd.DataFrame:
    """Load close prices for given tickers from the database."""
    conn = sqlite3.connect(DB_PATH)
    placeholders = ",".join("?" * len(tickers))
    query = f"""
        SELECT date, ticker, close
        FROM stock_prices
        WHERE ticker IN ({placeholders})
        ORDER BY date
    """
    df = pd.read_sql_query(query, conn, params=tickers, parse_dates=["date"])
    conn.close()
    pivot = df.pivot(index="date", columns="ticker", values="close")
    if period_days:
        pivot = pivot.iloc[-period_days:]
    return pivot


def portfolio_returns(prices: pd.DataFrame, weights: dict) -> pd.Series:
    """Compute daily portfolio returns given price DataFrame and weight dict."""
    tickers = [t for t in weights if t in prices.columns]
    w = np.array([weights[t] for t in tickers], dtype=float)
    w /= w.sum()
    daily_ret = prices[tickers].pct_change().dropna()
    port_ret = daily_ret.values @ w
    return pd.Series(port_ret, index=daily_ret.index, name="portfolio_return")


def portfolio_metrics(port_ret: pd.Series) -> dict:
    """Compute annualised return, volatility, Sharpe, and max drawdown."""
    ann_ret  = port_ret.mean() * 252
    ann_vol  = port_ret.std() * np.sqrt(252)
    sharpe   = ann_ret / ann_vol if ann_vol else 0.0
    cum      = (1 + port_ret).cumprod()
    drawdown = (cum - cum.cummax()) / cum.cummax()
    max_dd   = drawdown.min()
    return {
        "ann_return_pct":   round(ann_ret * 100, 2),
        "ann_volatility_pct": round(ann_vol * 100, 2),
        "sharpe_ratio":     round(sharpe, 3),
        "max_drawdown_pct": round(max_dd * 100, 2),
    }


def current_weights(prices: pd.DataFrame, weights: dict) -> dict:
    """Return market-value weights after price drift from equal starting shares."""
    tickers = [t for t in weights if t in prices.columns]
    latest  = prices[tickers].iloc[-1]
    initial = prices[tickers].iloc[0]
    shares  = {t: weights[t] / initial[t] for t in tickers}
    mv      = {t: shares[t] * latest[t] for t in tickers}
    total   = sum(mv.values())
    return {t: round(mv[t] / total * 100, 2) for t in tickers}


if __name__ == "__main__":
    prices  = load_prices(list(DEFAULT_PORTFOLIO.keys()))
    ret     = portfolio_returns(prices, DEFAULT_PORTFOLIO)
    metrics = portfolio_metrics(ret)
    print("Portfolio Metrics (1Y):")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    print("\nDrift-adjusted weights:")
    for t, w in current_weights(prices, DEFAULT_PORTFOLIO).items():
        print(f"  {t}: {w}%")
