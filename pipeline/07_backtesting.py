"""
Step 8 – Backtesting.

Strategy: ML Signal-Based Long-Only
  • Use the best trained model's out-of-sample predictions (last 20% of data).
  • Go long if predicted probability of UP > 0.55, else stay in cash.
  • Compare vs. Buy-and-Hold benchmark.

Metrics computed:
  Total Return, CAGR, Sharpe Ratio, Max Drawdown,
  Win Rate, Avg Win, Avg Loss, Profit Factor.

Outputs:
  reports/backtest_results.csv
  reports/figures/backtest_equity_<ticker>.png
"""

import os
import warnings
import joblib
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

FEATURES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "features")
MODELS_DIR   = os.path.join(os.path.dirname(__file__), "..", "models")
REPORTS_DIR  = os.path.join(os.path.dirname(__file__), "..", "reports")
FIGURES_DIR  = os.path.join(REPORTS_DIR, "figures")
TICKERS      = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
TARGET       = "Target_1d"
THRESHOLD    = 0.55
TEST_FRAC    = 0.20
EXCLUDE_COLS = ["Target_1d", "Target_5d", "Target_Return_1d", "Ticker",
                "Open", "High", "Low", "Close", "Volume"]


def cagr(equity: pd.Series) -> float:
    n_years = len(equity) / 252
    if n_years <= 0:
        return 0.0
    return (equity.iloc[-1] / equity.iloc[0]) ** (1 / n_years) - 1


def sharpe(returns: pd.Series, rf: float = 0.06) -> float:
    daily_rf = (1 + rf) ** (1/252) - 1
    excess   = returns - daily_rf
    if excess.std() == 0:
        return 0.0
    return (excess.mean() / excess.std()) * np.sqrt(252)


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd   = (equity - peak) / peak
    return dd.min()


def backtest_ticker(ticker: str) -> dict | None:
    ticker_slug = ticker.replace(".", "_")

    # Load artefact
    artefact_path = os.path.join(MODELS_DIR, f"{ticker_slug}_model.pkl")
    if not os.path.exists(artefact_path):
        print(f"  [{ticker}] Model not found – skipping")
        return None
    artefact = joblib.load(artefact_path)
    model, scaler, feature_cols = artefact["model"], artefact["scaler"], artefact["features"]

    # Load feature dataset
    ml_df = pd.read_csv(os.path.join(FEATURES_DIR, "ml_dataset.csv"),
                        parse_dates=["Date"], index_col="Date")
    df = ml_df[ml_df["Ticker"] == ticker].sort_index()

    # Test set = last 20%
    split = int(len(df) * (1 - TEST_FRAC))
    df_test = df.iloc[split:].copy()

    X_test  = df_test[feature_cols].values
    X_scaled = scaler.transform(X_test)
    probs    = model.predict_proba(X_scaled)[:, 1]

    df_test["Signal"]   = (probs >= THRESHOLD).astype(int)
    df_test["Prob_Up"]  = probs

    # Load raw close for the test period
    feat_file = os.path.join(FEATURES_DIR, f"{ticker_slug}_features.csv")
    raw = pd.read_csv(feat_file, parse_dates=["Date"], index_col="Date")
    raw = raw[["Close"]].loc[df_test.index]
    df_test["Close"] = raw["Close"]

    # Daily returns
    df_test["Daily_Return"]   = df_test["Close"].pct_change().fillna(0)

    # Strategy: apply signal from previous day (shift 1 to avoid lookahead)
    df_test["Strat_Return"]   = df_test["Signal"].shift(1).fillna(0) * df_test["Daily_Return"]
    df_test["BnH_Return"]     = df_test["Daily_Return"]

    # Equity curves (start at 100)
    df_test["Equity_Strat"]   = (1 + df_test["Strat_Return"]).cumprod() * 100
    df_test["Equity_BnH"]     = (1 + df_test["BnH_Return"]).cumprod() * 100

    # ── Metrics ───────────────────────────────────────────────────────────────
    strat_ret = df_test["Strat_Return"]
    bnh_ret   = df_test["BnH_Return"]

    wins  = strat_ret[strat_ret > 0]
    losses= strat_ret[strat_ret < 0]
    profit_factor = (wins.sum() / abs(losses.sum())) if losses.sum() != 0 else np.nan
    trades = df_test["Signal"].shift(1).fillna(0)
    n_trades = int(trades.sum())

    metrics = {
        "Ticker":              ticker,
        "Test_Start":          str(df_test.index[0].date()),
        "Test_End":            str(df_test.index[-1].date()),
        "N_Test_Days":         len(df_test),
        "N_Long_Days":         n_trades,
        "Strat_Total_Return_%":round((df_test["Equity_Strat"].iloc[-1]/100 - 1)*100, 2),
        "BnH_Total_Return_%":  round((df_test["Equity_BnH"].iloc[-1]/100 - 1)*100, 2),
        "Strat_CAGR_%":        round(cagr(df_test["Equity_Strat"]) * 100, 2),
        "BnH_CAGR_%":          round(cagr(df_test["Equity_BnH"])   * 100, 2),
        "Strat_Sharpe":        round(sharpe(strat_ret), 3),
        "BnH_Sharpe":          round(sharpe(bnh_ret),   3),
        "Strat_MaxDD_%":       round(max_drawdown(df_test["Equity_Strat"]) * 100, 2),
        "BnH_MaxDD_%":         round(max_drawdown(df_test["Equity_BnH"])   * 100, 2),
        "Win_Rate_%":          round(len(wins) / max(len(strat_ret[strat_ret != 0]), 1) * 100, 2),
        "Avg_Win_%":           round(wins.mean()   * 100 if len(wins)   else 0, 4),
        "Avg_Loss_%":          round(losses.mean() * 100 if len(losses) else 0, 4),
        "Profit_Factor":       round(profit_factor, 3) if not np.isnan(profit_factor) else "N/A",
    }

    # ── Equity curve chart ─────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(df_test.index, df_test["Equity_Strat"], label="ML Strategy", color="#2196F3", lw=2)
    ax.plot(df_test.index, df_test["Equity_BnH"],   label="Buy & Hold",  color="#FF9800", lw=2, ls="--")
    ax.fill_between(df_test.index, df_test["Equity_Strat"], 100,
                    where=df_test["Equity_Strat"] >= 100, alpha=0.15, color="#2196F3")
    ax.fill_between(df_test.index, df_test["Equity_Strat"], 100,
                    where=df_test["Equity_Strat"] <  100, alpha=0.15, color="#EF5350")
    ax.axhline(100, color="gray", ls=":", lw=1)
    ax.set_title(f"Backtest – {ticker}  |  ML Strategy vs Buy & Hold",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Date"); ax.set_ylabel("Equity (₹100 initial)")
    ax.legend(); ax.grid(alpha=0.25)
    fig.tight_layout()
    fname = os.path.join(FIGURES_DIR, f"backtest_equity_{ticker_slug}.png")
    plt.savefig(fname, dpi=140, bbox_inches="tight"); plt.close()
    print(f"  [{ticker}]  Strat={metrics['Strat_Total_Return_%']}%  "
          f"BnH={metrics['BnH_Total_Return_%']}%  "
          f"Sharpe={metrics['Strat_Sharpe']}  "
          f"MaxDD={metrics['Strat_MaxDD_%']}%")

    # Save per-ticker detailed trades
    trades_path = os.path.join(REPORTS_DIR,
                               f"backtest_trades_{ticker_slug}.csv")
    df_test[["Close", "Signal", "Prob_Up", "Strat_Return",
             "Equity_Strat", "Equity_BnH"]].to_csv(trades_path)

    return metrics


def main():
    os.makedirs(FIGURES_DIR, exist_ok=True)
    results = []
    for ticker in TICKERS:
        m = backtest_ticker(ticker)
        if m:
            results.append(m)

    results_df = pd.DataFrame(results)
    out_path = os.path.join(REPORTS_DIR, "backtest_results.csv")
    results_df.to_csv(out_path, index=False)
    print(f"\nBacktest results saved → {out_path}")
    print(results_df[["Ticker", "Strat_Total_Return_%", "BnH_Total_Return_%",
                       "Strat_Sharpe", "Strat_MaxDD_%"]].to_string(index=False))


if __name__ == "__main__":
    main()
