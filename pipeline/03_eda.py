"""
Step 3 – Exploratory Data Analysis.
Produces publication-quality charts saved to reports/figures/:
  • price_history.png       – adjusted close for all 5 tickers
  • daily_returns_dist.png  – histogram + KDE of daily returns
  • correlation_heatmap.png – pairwise return correlation
  • volatility_rolling.png  – 30-day rolling volatility
  • volume_trend.png        – 30-day rolling average volume
  • candlestick_<ticker>.png– 90-day candlestick sample
Summary stats saved to reports/eda_summary.csv
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from matplotlib.patches import Patch

CLEANED_DIR  = os.path.join(os.path.dirname(__file__), "..", "data", "cleaned")
FIGURES_DIR  = os.path.join(os.path.dirname(__file__), "..", "reports", "figures")
REPORTS_DIR  = os.path.join(os.path.dirname(__file__), "..", "reports")
TICKERS      = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
SHORT_NAMES  = {"RELIANCE.NS": "Reliance", "TCS.NS": "TCS",
                "INFY.NS": "Infosys", "HDFCBANK.NS": "HDFC Bank",
                "ICICIBANK.NS": "ICICI Bank"}
PALETTE      = ["#2196F3", "#F44336", "#4CAF50", "#FF9800", "#9C27B0"]


# ── helpers ──────────────────────────────────────────────────────────────────

def load_cleaned(ticker: str) -> pd.DataFrame:
    fname = f"{ticker.replace('.', '_')}_cleaned.csv"
    df    = pd.read_csv(os.path.join(CLEANED_DIR, fname),
                        parse_dates=["Date"], index_col="Date")
    return df


def savefig(name: str):
    path = os.path.join(FIGURES_DIR, name)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path}")


# ── plot functions ────────────────────────────────────────────────────────────

def plot_price_history(data: dict):
    fig, ax = plt.subplots(figsize=(14, 6))
    for i, (ticker, df) in enumerate(data.items()):
        norm = df["Close"] / df["Close"].iloc[0] * 100
        ax.plot(df.index, norm, color=PALETTE[i], label=SHORT_NAMES[ticker], lw=1.5)
    ax.set_title("Normalised Closing Price (Base = 100)", fontsize=15, fontweight="bold")
    ax.set_xlabel("Date"); ax.set_ylabel("Index (base 100)")
    ax.legend(loc="upper left"); ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.tight_layout()
    savefig("price_history.png")


def plot_returns_distribution(returns: pd.DataFrame):
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    axes = axes.flatten()
    for i, col in enumerate(returns.columns):
        ax = axes[i]
        data = returns[col].dropna()
        ax.hist(data, bins=80, color=PALETTE[i], alpha=0.6, density=True)
        data.plot.kde(ax=ax, color=PALETTE[i], lw=2)
        ax.axvline(data.mean(), color="black", ls="--", lw=1, label=f"μ={data.mean():.4f}")
        ax.axvline(data.std(),  color="red",   ls=":",  lw=1)
        ax.set_title(SHORT_NAMES[col]); ax.legend(fontsize=8)
        ax.set_xlabel("Daily Return"); ax.set_ylabel("Density")
    axes[-1].set_visible(False)
    fig.suptitle("Daily Return Distribution (2018–2024)", fontsize=14, fontweight="bold")
    fig.tight_layout()
    savefig("daily_returns_dist.png")


def plot_correlation_heatmap(returns: pd.DataFrame):
    corr = returns.corr()
    short = {t: SHORT_NAMES[t] for t in TICKERS}
    corr.rename(columns=short, index=short, inplace=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm",
                vmin=-1, vmax=1, ax=ax, linewidths=0.5,
                annot_kws={"size": 11})
    ax.set_title("Pairwise Return Correlation", fontsize=14, fontweight="bold")
    fig.tight_layout()
    savefig("correlation_heatmap.png")


def plot_rolling_volatility(returns: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(14, 6))
    for i, col in enumerate(returns.columns):
        vol = returns[col].rolling(30).std() * np.sqrt(252)
        ax.plot(vol.index, vol, color=PALETTE[i],
                label=SHORT_NAMES[col], lw=1.4, alpha=0.85)
    ax.set_title("30-Day Rolling Annualised Volatility", fontsize=15, fontweight="bold")
    ax.set_xlabel("Date"); ax.set_ylabel("Annualised Volatility")
    ax.legend(); ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.tight_layout()
    savefig("volatility_rolling.png")


def plot_volume_trend(data: dict):
    fig, ax = plt.subplots(figsize=(14, 6))
    for i, (ticker, df) in enumerate(data.items()):
        vol = df["Volume"].rolling(30).mean()
        ax.plot(df.index, vol / 1e6, color=PALETTE[i],
                label=SHORT_NAMES[ticker], lw=1.4, alpha=0.85)
    ax.set_title("30-Day Rolling Average Volume (Million shares)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date"); ax.set_ylabel("Volume (M)")
    ax.legend(); ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.tight_layout()
    savefig("volume_trend.png")


def plot_candlestick(df: pd.DataFrame, ticker: str):
    sample = df.tail(90).copy()
    fig, ax = plt.subplots(figsize=(14, 5))
    for i, (date, row) in enumerate(sample.iterrows()):
        color = "#26A69A" if row["Close"] >= row["Open"] else "#EF5350"
        ax.plot([i, i], [row["Low"], row["High"]], color=color, lw=1)
        ax.bar(i, abs(row["Close"] - row["Open"]),
               bottom=min(row["Open"], row["Close"]),
               color=color, width=0.6, alpha=0.9)
    ticks = range(0, len(sample), 10)
    ax.set_xticks(list(ticks))
    ax.set_xticklabels([sample.index[t].strftime("%b %d") for t in ticks], rotation=30)
    ax.set_title(f"{SHORT_NAMES[ticker]} – Last 90 Trading Days (Candlestick)",
                 fontsize=13, fontweight="bold")
    ax.set_ylabel("Price (₹)"); ax.grid(alpha=0.2, axis="y")
    green_patch = Patch(color="#26A69A", label="Bullish")
    red_patch   = Patch(color="#EF5350", label="Bearish")
    ax.legend(handles=[green_patch, red_patch])
    fig.tight_layout()
    savefig(f"candlestick_{ticker.replace('.', '_')}.png")


def summary_stats(data: dict, returns: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ticker, df in data.items():
        r = returns[ticker].dropna()
        ann_ret = (1 + r.mean()) ** 252 - 1
        ann_vol = r.std() * np.sqrt(252)
        sharpe  = ann_ret / ann_vol if ann_vol > 0 else np.nan
        max_dd  = (df["Close"] / df["Close"].cummax() - 1).min()
        rows.append({
            "Ticker":          ticker,
            "Name":            SHORT_NAMES[ticker],
            "Total_Trading_Days": len(df),
            "Start_Price_INR": round(df["Close"].iloc[0],  2),
            "End_Price_INR":   round(df["Close"].iloc[-1], 2),
            "Total_Return_%":  round((df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100, 2),
            "Ann_Return_%":    round(ann_ret * 100, 2),
            "Ann_Volatility_%":round(ann_vol * 100, 2),
            "Sharpe_Ratio":    round(sharpe, 3),
            "Max_Drawdown_%":  round(max_dd  * 100, 2),
            "Avg_Volume_M":    round(df["Volume"].mean() / 1e6, 3),
        })
    return pd.DataFrame(rows)


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(FIGURES_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    data = {t: load_cleaned(t) for t in TICKERS}
    returns = pd.DataFrame({t: data[t]["Close"].pct_change() for t in TICKERS})

    print("Generating EDA charts …")
    plot_price_history(data)
    plot_returns_distribution(returns)
    plot_correlation_heatmap(returns)
    plot_rolling_volatility(returns)
    plot_volume_trend(data)
    for ticker, df in data.items():
        plot_candlestick(df, ticker)

    stats = summary_stats(data, returns)
    stats_path = os.path.join(REPORTS_DIR, "eda_summary.csv")
    stats.to_csv(stats_path, index=False)
    print(f"\nEDA Summary:\n{stats.to_string(index=False)}")
    print(f"\nAll charts saved to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
