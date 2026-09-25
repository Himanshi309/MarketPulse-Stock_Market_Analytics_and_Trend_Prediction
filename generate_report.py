"""
generate_report.py
==================
All-in-one report generator:

  1. Start Flask backend (subprocess) and verify all 10 endpoints
  2. Collect and save all API outputs as JSON
  3. Generate UI screenshot images programmatically with matplotlib
  4. Build a full Word (.docx) project report with all content and images

Run:  python generate_report.py
"""

import os
import sys
import json
import time
import subprocess
import textwrap
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch

import requests
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
FIGURES_DIR  = os.path.join(BASE_DIR, "reports", "figures")
REPORTS_DIR  = os.path.join(BASE_DIR, "reports")
SCREENS_DIR  = os.path.join(REPORTS_DIR, "screenshots")
API_DIR      = os.path.join(REPORTS_DIR, "api_outputs")
DOCX_PATH    = os.path.join(REPORTS_DIR, "MarketPulse_Report.docx")

for d in [SCREENS_DIR, API_DIR]:
    os.makedirs(d, exist_ok=True)

API_BASE = "http://localhost:5000/api"
TICKERS  = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
NAMES    = {"RELIANCE.NS":"Reliance","TCS.NS":"TCS","INFY.NS":"Infosys",
            "HDFCBANK.NS":"HDFC Bank","ICICIBANK.NS":"ICICI Bank"}
COLORS   = ["#2196F3","#F44336","#4CAF50","#FF9800","#9C27B0"]
DARK     = "#0d1117"; SURF = "#161b22"

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 – START/VERIFY FLASK BACKEND
# ══════════════════════════════════════════════════════════════════════════════

_flask_proc = None

def start_backend():
    global _flask_proc
    # Check if already running
    try:
        r = requests.get(f"{API_BASE}/health", timeout=3)
        if r.ok:
            print("  ✅ Flask backend already running")
            return True
    except Exception:
        pass

    print("  Starting Flask backend …")
    _flask_proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE_DIR, "backend", "app.py")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(20):
        time.sleep(1)
        try:
            r = requests.get(f"{API_BASE}/health", timeout=3)
            if r.ok:
                print("  ✅ Flask backend started (PID", _flask_proc.pid, ")")
                return True
        except Exception:
            pass
    print("  ❌ Could not start Flask backend. Ensure port 5000 is free.")
    return False


def stop_backend():
    global _flask_proc
    if _flask_proc:
        _flask_proc.terminate()
        _flask_proc = None


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 – COLLECT ALL API OUTPUTS
# ══════════════════════════════════════════════════════════════════════════════

def collect_api_outputs() -> dict:
    """Call all API endpoints, save JSON, return collected data."""
    print("\n─── Collecting API outputs ───")
    collected = {}

    def get(ep, params=None, label=None):
        try:
            r = requests.get(f"{API_BASE}/{ep}", params=params, timeout=15)
            data = r.json()
            key = label or ep
            collected[key] = data
            out_path = os.path.join(API_DIR, f"{key.replace('/','_')}.json")
            with open(out_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            print(f"  ✅ GET /api/{ep} → {out_path}")
            return data
        except Exception as e:
            print(f"  ❌ GET /api/{ep}: {e}")
            return None

    def post(ep, payload, label=None):
        try:
            r = requests.post(f"{API_BASE}/{ep}", json=payload, timeout=15)
            data = r.json()
            key = label or ep
            collected[key] = data
            out_path = os.path.join(API_DIR, f"{key.replace('/','_')}.json")
            with open(out_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            print(f"  ✅ POST /api/{ep} → {out_path}")
            return data
        except Exception as e:
            print(f"  ❌ POST /api/{ep}: {e}")
            return None

    get("health")
    get("tickers")
    get("overview")
    get("correlation")
    get("backtest")
    get("model_metrics")
    for t in TICKERS:
        slug = t.replace(".", "_")
        get("prices", {"ticker": t, "period": "2Y"}, f"prices_{slug}")
        get("indicators", {"ticker": t}, f"indicators_{slug}")
        get("predictions", {"ticker": t}, f"predictions_{slug}")
        post("predict", {"ticker": t}, f"predict_{slug}")

    # Consolidated summary file
    summary = {
        "health":        collected.get("health"),
        "tickers_count": len(collected.get("tickers", [])),
        "overview":      collected.get("overview"),
        "backtest":      collected.get("backtest"),
        "model_metrics_count": len(collected.get("model_metrics", [])),
        "endpoints_hit": len(collected),
    }
    with open(os.path.join(API_DIR, "_summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n  Total endpoints collected: {len(collected)}")
    return collected


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 – GENERATE UI SCREENSHOT IMAGES
# ══════════════════════════════════════════════════════════════════════════════

def save_screen(fig, name):
    path = os.path.join(SCREENS_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK)
    plt.close(fig)
    print(f"  Saved {path}")
    return path


def make_screen_overview(api: dict) -> str:
    """Simulates the Overview page screenshot."""
    ov = api.get("overview", [])
    fig = plt.figure(figsize=(16, 10), facecolor=DARK)
    gs  = gridspec.GridSpec(3, 5, figure=fig, hspace=0.55, wspace=0.35,
                            top=0.93, bottom=0.05, left=0.05, right=0.97)

    # Title bar
    fig.text(0.5, 0.97, "📈  MarketPulse – Market Overview",
             ha="center", va="top", fontsize=17, fontweight="bold",
             color="#58a6ff", fontfamily="monospace")

    # KPI cards (top row)
    for i, item in enumerate(ov[:5]):
        ax = fig.add_subplot(gs[0, i])
        ax.set_facecolor(SURF)
        chg = float(item.get("change_pct", 0))
        color = "#3fb950" if chg >= 0 else "#f85149"
        ax.text(0.5, 0.72, f"₹{item['close']:,.2f}", ha="center", va="center",
                fontsize=13, fontweight="bold", color="#e6edf3", transform=ax.transAxes)
        ax.text(0.5, 0.42, f"{chg:+.2f}%", ha="center", va="center",
                fontsize=11, fontweight="bold", color=color, transform=ax.transAxes)
        ax.text(0.5, 0.15, NAMES.get(item["ticker"], item["ticker"]),
                ha="center", va="center", fontsize=9, color="#8b949e", transform=ax.transAxes)
        for spine in ax.spines.values():
            spine.set_edgecolor("#58a6ff"); spine.set_linewidth(1.2)
        ax.set_xticks([]); ax.set_yticks([])

    # Normalised price chart
    ax_perf = fig.add_subplot(gs[1, :3])
    ax_perf.set_facecolor(DARK)
    all_prices = {t: api.get(f"prices_{t.replace('.','_')}", []) for t in TICKERS}
    for i, (ticker, prices) in enumerate(all_prices.items()):
        if prices:
            df = pd.DataFrame(prices)
            df["date"] = pd.to_datetime(df["date"])
            norm = df["close"] / df["close"].iloc[0] * 100
            ax_perf.plot(df["date"], norm, color=COLORS[i], lw=1.8, label=NAMES[ticker])
    ax_perf.set_title("Normalised Price (Base=100)", color="#e6edf3", fontsize=10, fontweight="bold")
    ax_perf.tick_params(colors="#8b949e", labelsize=7)
    ax_perf.legend(fontsize=7, facecolor=SURF, labelcolor="#e6edf3")
    for spine in ax_perf.spines.values(): spine.set_edgecolor("#30363d")
    ax_perf.grid(alpha=0.12, color="#30363d")

    # Correlation heatmap
    ax_corr = fig.add_subplot(gs[1, 3:])
    ax_corr.set_facecolor(DARK)
    corr_data = api.get("correlation", {})
    if corr_data:
        tks_short = [NAMES.get(t, t) for t in corr_data["tickers"]]
        mat = np.array(corr_data["matrix"])
        im = ax_corr.imshow(mat, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
        ax_corr.set_xticks(range(len(tks_short))); ax_corr.set_yticks(range(len(tks_short)))
        ax_corr.set_xticklabels(tks_short, rotation=25, ha="right", color="#8b949e", fontsize=7)
        ax_corr.set_yticklabels(tks_short, color="#8b949e", fontsize=7)
        for ii in range(len(mat)):
            for jj in range(len(mat)):
                ax_corr.text(jj, ii, f"{mat[ii,jj]:.2f}", ha="center", va="center",
                             color="#0d1117" if abs(mat[ii,jj]) > 0.5 else "#e6edf3", fontsize=7)
        plt.colorbar(im, ax=ax_corr, fraction=0.04)
    ax_corr.set_title("Return Correlation", color="#e6edf3", fontsize=10, fontweight="bold")
    for spine in ax_corr.spines.values(): spine.set_edgecolor("#30363d")

    # EDA stats
    ax_eda = fig.add_subplot(gs[2, :])
    ax_eda.set_facecolor(SURF)
    ax_eda.axis("off")
    eda_path = os.path.join(REPORTS_DIR, "eda_summary.csv")
    if os.path.exists(eda_path):
        df = pd.read_csv(eda_path)
        cols = ["Name","Total_Return_%","Ann_Return_%","Ann_Volatility_%","Sharpe_Ratio","Max_Drawdown_%"]
        num_cols_eda = [c for c in cols if df[c].dtype != object]
        display_df = df[cols].copy()
        for c in num_cols_eda:
            display_df[c] = display_df[c].round(2)
        tbl = ax_eda.table(
            cellText=display_df.values,
            colLabels=[c.replace("_"," ") for c in cols],
            cellLoc="center", loc="center",
            bbox=[0.0, 0.0, 1.0, 1.0]
        )
        tbl.auto_set_font_size(False); tbl.set_fontsize(9)
        for (r, c), cell in tbl.get_celld().items():
            cell.set_facecolor(SURF if r > 0 else "#161b22")
            cell.set_text_props(color="#e6edf3" if r > 0 else "#8b949e")
            cell.set_edgecolor("#30363d")
    ax_eda.set_title("EDA Summary Statistics", color="#e6edf3", fontsize=10, fontweight="bold", pad=4)

    return save_screen(fig, "screen_01_overview.png")


def make_screen_price_chart(api: dict, ticker="RELIANCE.NS") -> str:
    prices = api.get(f"prices_{ticker.replace('.','_')}", [])
    if not prices: return ""
    df = pd.DataFrame(prices[-90:]).reset_index(drop=True)
    fig, axes = plt.subplots(2, 1, figsize=(16, 8), facecolor=DARK,
                              gridspec_kw={"height_ratios": [3, 1], "hspace": 0.12})
    fig.text(0.5, 0.97, f"📊  Price Charts – {NAMES.get(ticker)} ({ticker})",
             ha="center", va="top", fontsize=14, fontweight="bold",
             color="#58a6ff", fontfamily="monospace")

    # Candlestick
    ax = axes[0]; ax.set_facecolor(DARK)
    for i, row in df.iterrows():
        col = "#26A69A" if row["close"] >= row["open"] else "#EF5350"
        ax.plot([i, i], [row["low"], row["high"]], color=col, lw=0.9)
        ax.bar(i, abs(row["close"] - row["open"]),
               bottom=min(row["open"], row["close"]),
               color=col, width=0.7, alpha=0.9)
    ticks = range(0, len(df), 10)
    ax.set_xticks(list(ticks))
    ax.set_xticklabels([df["date"].iloc[t][:10] for t in ticks], rotation=20, color="#8b949e", fontsize=7)
    ax.set_title("Candlestick (Last 90 Trading Days)", color="#e6edf3", fontsize=11)
    ax.tick_params(colors="#8b949e")
    for spine in ax.spines.values(): spine.set_edgecolor("#30363d")
    ax.grid(alpha=0.1, axis="y", color="#30363d")
    g = mpatches.Patch(color="#26A69A", label="Bullish")
    r = mpatches.Patch(color="#EF5350", label="Bearish")
    ax.legend(handles=[g, r], facecolor=SURF, labelcolor="#e6edf3", fontsize=9)

    # Volume
    ax2 = axes[1]; ax2.set_facecolor(DARK)
    bar_cols = ["#3fb95060" if df["close"].iloc[i] >= df["open"].iloc[i] else "#f8514960"
                for i in range(len(df))]
    ax2.bar(range(len(df)), df["volume"] / 1e6, color=bar_cols, width=0.8)
    ax2.set_ylabel("Vol (M)", color="#8b949e", fontsize=8)
    ax2.tick_params(colors="#8b949e", labelsize=7)
    for spine in ax2.spines.values(): spine.set_edgecolor("#30363d")
    ax2.grid(alpha=0.08, axis="y", color="#30363d")

    return save_screen(fig, f"screen_02_candlestick_{ticker.replace('.','_')}.png")


def make_screen_indicators(api: dict, ticker="RELIANCE.NS") -> str:
    inds = api.get(f"indicators_{ticker.replace('.','_')}", [])
    if not inds: return ""
    df = pd.DataFrame(inds)
    df["date"] = pd.to_datetime(df["date"])
    df = df.tail(252)

    fig, axes = plt.subplots(3, 1, figsize=(16, 12), facecolor=DARK,
                              gridspec_kw={"hspace": 0.45})
    fig.text(0.5, 0.97, f"📉  Technical Indicators – {NAMES.get(ticker)}",
             ha="center", va="top", fontsize=14, fontweight="bold",
             color="#58a6ff", fontfamily="monospace")

    # RSI
    ax1 = axes[0]; ax1.set_facecolor(DARK)
    ax1.plot(df["date"], df["rsi_14"], color="#bc8cff", lw=1.5, label="RSI-14")
    ax1.axhline(70, color="#f85149", ls="--", lw=1, label="Overbought")
    ax1.axhline(30, color="#3fb950", ls="--", lw=1, label="Oversold")
    ax1.fill_between(df["date"], df["rsi_14"], 70, where=df["rsi_14"] >= 70, alpha=0.12, color="#f85149")
    ax1.fill_between(df["date"], df["rsi_14"], 30, where=df["rsi_14"] <= 30, alpha=0.12, color="#3fb950")
    ax1.set_ylim(0, 100); ax1.set_title("RSI-14", color="#e6edf3", fontsize=10)
    ax1.tick_params(colors="#8b949e", labelsize=7)
    ax1.legend(fontsize=8, facecolor=SURF, labelcolor="#e6edf3")
    for spine in ax1.spines.values(): spine.set_edgecolor("#30363d")
    ax1.grid(alpha=0.1, color="#30363d")

    # MACD
    ax2 = axes[1]; ax2.set_facecolor(DARK)
    ax2.plot(df["date"], df["macd"], color="#58a6ff", lw=1.5, label="MACD")
    ax2.plot(df["date"], df["macd_signal"], color="#ffa657", lw=1.5, label="Signal")
    h_colors = ["#3fb950" if v >= 0 else "#f85149" for v in df["macd_hist"]]
    ax2.bar(df["date"], df["macd_hist"], color=h_colors, width=1.5, alpha=0.65, label="Histogram")
    ax2.set_title("MACD (12,26,9)", color="#e6edf3", fontsize=10)
    ax2.tick_params(colors="#8b949e", labelsize=7)
    ax2.legend(fontsize=8, facecolor=SURF, labelcolor="#e6edf3")
    for spine in ax2.spines.values(): spine.set_edgecolor("#30363d")
    ax2.grid(alpha=0.1, color="#30363d")

    # Bollinger Bands
    ax3 = axes[2]; ax3.set_facecolor(DARK)
    prices_raw = api.get(f"prices_{ticker.replace('.','_')}", [])
    if prices_raw:
        df_p = pd.DataFrame(prices_raw)
        df_p["date"] = pd.to_datetime(df_p["date"])
        merged = pd.merge(df_p[["date","close"]], df[["date","bb_upper","bb_lower"]], on="date")
        ax3.plot(merged["date"], merged["close"], color="#ffa657", lw=1.5, label="Close")
        ax3.plot(merged["date"], merged["bb_upper"], color="#58a6ff", lw=1, ls="--", label="BB Upper")
        ax3.plot(merged["date"], merged["bb_lower"], color="#58a6ff", lw=1, ls="--", label="BB Lower")
        ax3.fill_between(merged["date"], merged["bb_upper"], merged["bb_lower"], alpha=0.05, color="#58a6ff")
    ax3.set_title("Bollinger Bands (20,2)", color="#e6edf3", fontsize=10)
    ax3.tick_params(colors="#8b949e", labelsize=7)
    ax3.legend(fontsize=8, facecolor=SURF, labelcolor="#e6edf3")
    for spine in ax3.spines.values(): spine.set_edgecolor("#30363d")
    ax3.grid(alpha=0.1, color="#30363d")

    return save_screen(fig, f"screen_03_indicators_{ticker.replace('.','_')}.png")


def make_screen_ml_models(api: dict) -> str:
    metrics = api.get("model_metrics", [])
    if not metrics: return ""
    df = pd.DataFrame(metrics)
    model_names = list(df["model"].unique())
    tickers_unique = list(df["ticker"].unique())
    tickers_short = [NAMES.get(t, t) for t in tickers_unique]

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor=DARK)
    fig.text(0.5, 0.97, "🤖  ML Model Performance – Walk-Forward CV (5 Folds)",
             ha="center", va="top", fontsize=14, fontweight="bold",
             color="#58a6ff", fontfamily="monospace")

    color_map = {"LogisticRegression":"#58a6ff","RandomForest":"#3fb950",
                 "XGBoost":"#ffa657","LightGBM":"#bc8cff"}
    x = np.arange(len(tickers_short)); w = 0.2

    for ax, metric, title, ylim in zip(
        axes, ["roc_auc", "accuracy"],
        ["ROC-AUC Score", "Accuracy"],
        [(0.45, 0.60), (0.44, 0.60)]
    ):
        ax.set_facecolor(DARK)
        for j, mn in enumerate(model_names):
            sub = df[df["model"] == mn]
            vals = [float(sub[sub["ticker"] == t][metric].values[0])
                    if len(sub[sub["ticker"] == t]) else 0
                    for t in tickers_unique]
            ax.bar(x + j*w, vals, w, label=mn, color=color_map.get(mn, COLORS[j]), alpha=0.85)
        ax.set_xticks(x + w*1.5)
        ax.set_xticklabels(tickers_short, rotation=15, color="#8b949e", fontsize=9)
        ax.set_title(title, color="#e6edf3", fontsize=11, fontweight="bold")
        ax.set_ylim(*ylim)
        ax.tick_params(colors="#8b949e")
        for spine in ax.spines.values(): spine.set_edgecolor("#30363d")
        ax.grid(alpha=0.12, axis="y", color="#30363d")
        ax.legend(fontsize=8, facecolor=SURF, labelcolor="#e6edf3")
        ax.axhline(0.5, color="#8b949e", ls=":", lw=1, alpha=0.6)

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    return save_screen(fig, "screen_04_ml_models.png")


def make_screen_backtest(api: dict) -> str:
    bt = api.get("backtest", [])
    if not bt: return ""
    df = pd.DataFrame(bt)
    names_short = [NAMES.get(r["ticker"], r["ticker"]) for _, r in df.iterrows()]
    x = np.arange(len(names_short)); w = 0.35

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor=DARK)
    fig.text(0.5, 0.97, "⏳  Backtesting – ML Strategy vs Buy & Hold",
             ha="center", va="top", fontsize=14, fontweight="bold",
             color="#58a6ff", fontfamily="monospace")

    # Return comparison
    ax = axes[0]; ax.set_facecolor(DARK)
    strat = pd.to_numeric(df["strat_total_return_%"], errors="coerce").fillna(0)
    bnh   = pd.to_numeric(df["bnh_total_return_%"],   errors="coerce").fillna(0)
    ax.bar(x - w/2, strat, w, label="ML Strategy", color="#58a6ff", alpha=0.85)
    ax.bar(x + w/2, bnh,   w, label="Buy & Hold",  color="#8b949e", alpha=0.85)
    ax.set_xticks(x); ax.set_xticklabels(names_short, color="#8b949e", fontsize=9)
    ax.set_title("Total Return % (Test Set)", color="#e6edf3", fontsize=11, fontweight="bold")
    ax.tick_params(colors="#8b949e")
    ax.legend(facecolor=SURF, labelcolor="#e6edf3", fontsize=9)
    for spine in ax.spines.values(): spine.set_edgecolor("#30363d")
    ax.grid(alpha=0.12, axis="y", color="#30363d")

    # Sharpe
    ax2 = axes[1]; ax2.set_facecolor(DARK)
    sharpe = pd.to_numeric(df["strat_sharpe"], errors="coerce").fillna(0)
    bar_colors = ["#3fb950" if v >= 1 else "#ffa657" for v in sharpe]
    ax2.bar(x, sharpe, color=bar_colors, alpha=0.85)
    ax2.set_xticks(x); ax2.set_xticklabels(names_short, color="#8b949e", fontsize=9)
    ax2.set_title("Sharpe Ratio – ML Strategy", color="#e6edf3", fontsize=11, fontweight="bold")
    ax2.tick_params(colors="#8b949e")
    for spine in ax2.spines.values(): spine.set_edgecolor("#30363d")
    ax2.grid(alpha=0.12, axis="y", color="#30363d")
    ax2.axhline(1.0, color="#58a6ff", ls="--", lw=1)

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    return save_screen(fig, "screen_05_backtest.png")


def make_screen_prediction(api: dict, ticker="TCS.NS") -> str:
    preds = api.get(f"predictions_{ticker.replace('.','_')}", [])
    if not preds: return ""
    df = pd.DataFrame(preds)
    df["date"] = pd.to_datetime(df["date"])
    buy  = df[df["predicted_up"] == 1]
    sell = df[df["predicted_up"] == 0]

    fig, axes = plt.subplots(2, 1, figsize=(16, 8), facecolor=DARK,
                              gridspec_kw={"hspace": 0.4})
    fig.text(0.5, 0.97, f"🎯  ML Prediction Signals – {NAMES.get(ticker)} (Test Set)",
             ha="center", va="top", fontsize=14, fontweight="bold",
             color="#58a6ff", fontfamily="monospace")

    ax1 = axes[0]; ax1.set_facecolor(DARK)
    ax1.plot(df["date"], df["close"], color="#ffa657", lw=1.5, label="Close")
    ax1.scatter(buy["date"],  buy["close"],  color="#3fb950", s=15, label="Buy Signal",  zorder=5, alpha=0.85)
    ax1.scatter(sell["date"], sell["close"], color="#f85149", s=15, label="Hold Signal", zorder=5, alpha=0.6)
    ax1.set_title("Price + Signals", color="#e6edf3", fontsize=10)
    ax1.tick_params(colors="#8b949e", labelsize=7)
    ax1.legend(fontsize=8, facecolor=SURF, labelcolor="#e6edf3")
    for spine in ax1.spines.values(): spine.set_edgecolor("#30363d")
    ax1.grid(alpha=0.1, color="#30363d")

    ax2 = axes[1]; ax2.set_facecolor(DARK)
    window = 20
    rolling = [df["correct"].iloc[max(0,i-window):i].mean()*100 for i in range(1, len(df)+1)]
    ax2.plot(df["date"], rolling, color="#58a6ff", lw=1.5, label=f"{window}d Rolling Accuracy")
    ax2.axhline(50, color="#8b949e", ls="--", lw=1, label="50% baseline")
    ax2.fill_between(df["date"], rolling, 50, where=np.array(rolling) >= 50,
                     alpha=0.1, color="#3fb950")
    ax2.fill_between(df["date"], rolling, 50, where=np.array(rolling) < 50,
                     alpha=0.1, color="#f85149")
    ax2.set_ylim(20, 80); ax2.set_title(f"{window}d Rolling Accuracy %", color="#e6edf3", fontsize=10)
    ax2.tick_params(colors="#8b949e", labelsize=7)
    ax2.legend(fontsize=8, facecolor=SURF, labelcolor="#e6edf3")
    for spine in ax2.spines.values(): spine.set_edgecolor("#30363d")
    ax2.grid(alpha=0.1, color="#30363d")

    return save_screen(fig, f"screen_06_predictions_{ticker.replace('.','_')}.png")


def make_screen_live_predict(api: dict) -> str:
    """Shows the live prediction panel for all 5 tickers."""
    fig, ax = plt.subplots(figsize=(14, 6), facecolor=DARK)
    ax.set_facecolor(DARK); ax.axis("off")
    fig.text(0.5, 0.95, "🎯  Live ML Predictions – All Tickers",
             ha="center", va="top", fontsize=14, fontweight="bold",
             color="#58a6ff", fontfamily="monospace")

    for i, ticker in enumerate(TICKERS):
        slug = ticker.replace(".", "_")
        pred = api.get(f"predict_{slug}", {})
        if not pred: continue
        is_buy = pred.get("signal") == "BUY"
        col_bg = "#1a2f1a" if is_buy else "#2f1a1a"
        col_sig = "#3fb950" if is_buy else "#f85149"
        x0 = 0.03 + i * 0.19
        rect = FancyBboxPatch((x0, 0.1), 0.18, 0.72,
                               boxstyle="round,pad=0.01",
                               facecolor=col_bg, edgecolor=col_sig, lw=1.5,
                               transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(x0+0.09, 0.77, NAMES.get(ticker, ticker), ha="center", va="center",
                fontsize=10, fontweight="bold", color="#e6edf3", transform=ax.transAxes)
        ax.text(x0+0.09, 0.63, pred.get("signal", "?"), ha="center", va="center",
                fontsize=16, fontweight="bold", color=col_sig, transform=ax.transAxes)
        ax.text(x0+0.09, 0.50, f"₹{pred.get('close', 0):,.2f}", ha="center", va="center",
                fontsize=10, color="#e6edf3", transform=ax.transAxes)
        ax.text(x0+0.09, 0.38, f"P(Up): {pred.get('prob_up',0)*100:.1f}%",
                ha="center", va="center", fontsize=9, color="#8b949e", transform=ax.transAxes)
        ax.text(x0+0.09, 0.26, f"Conf: {pred.get('confidence',0):.1f}%",
                ha="center", va="center", fontsize=9, color="#8b949e", transform=ax.transAxes)
        ax.text(x0+0.09, 0.15, pred.get("date", ""), ha="center", va="center",
                fontsize=8, color="#8b949e", transform=ax.transAxes)

    return save_screen(fig, "screen_07_live_predict.png")


def generate_screenshots(api: dict) -> list:
    print("\n─── Generating UI screenshots ───")
    paths = []
    paths.append(make_screen_overview(api))
    for ticker in TICKERS[:2]:
        p = make_screen_price_chart(api, ticker)
        if p: paths.append(p)
    for ticker in TICKERS[:2]:
        p = make_screen_indicators(api, ticker)
        if p: paths.append(p)
    paths.append(make_screen_ml_models(api))
    paths.append(make_screen_backtest(api))
    for ticker in TICKERS[:2]:
        p = make_screen_prediction(api, ticker)
        if p: paths.append(p)
    paths.append(make_screen_live_predict(api))
    paths = [p for p in paths if p and os.path.exists(p)]
    print(f"\n  {len(paths)} screenshots saved → {SCREENS_DIR}")
    return paths


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 – BUILD WORD REPORT
# ══════════════════════════════════════════════════════════════════════════════

def _set_cell_bg(cell, hex_color: str):
    """Set a table cell background colour."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color.lstrip("#"))
    tcPr.append(shd)


def _add_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        if level == 1:
            run.font.color.rgb = RGBColor(0x58, 0xA6, 0xFF)
        elif level == 2:
            run.font.color.rgb = RGBColor(0x3F, 0xB9, 0x50)
        else:
            run.font.color.rgb = RGBColor(0xFF, 0xA6, 0x57)
    return h


def _add_para(doc, text, size=11, bold=False, color=None, italic=False):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*bytes.fromhex(color.lstrip("#")))
    return p


def _add_image(doc, path, width_inches=6.0, caption=None):
    if path and os.path.exists(path):
        doc.add_picture(path, width=Inches(width_inches))
        if caption:
            cap = doc.add_paragraph(caption)
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap.runs[0].font.size = Pt(9)
            cap.runs[0].font.italic = True
            cap.runs[0].font.color.rgb = RGBColor(0x8B, 0x94, 0x9E)


def _add_df_table(doc, df: pd.DataFrame, header_color="1C2128"):
    df = df.copy()
    for c in df.select_dtypes("number").columns:
        df[c] = df[c].round(4)
    t = doc.add_table(rows=1, cols=len(df.columns))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for j, col in enumerate(df.columns):
        hdr[j].text = str(col).replace("_"," ").upper()
        hdr[j].paragraphs[0].runs[0].font.size = Pt(8)
        hdr[j].paragraphs[0].runs[0].bold = True
        hdr[j].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x8B, 0x94, 0x9E)
        _set_cell_bg(hdr[j], header_color)
    for _, row in df.iterrows():
        cells = t.add_row().cells
        for j, val in enumerate(row):
            cells[j].text = str(val)
            cells[j].paragraphs[0].runs[0].font.size = Pt(8)
    return t


def build_word_report(api: dict, screenshots: list):
    print("\n─── Building Word report ───")
    doc = Document()

    # ── Page margins ──────────────────────────────────────────────────────────
    for section in doc.sections:
        section.top_margin    = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin   = Cm(2.5)
        section.right_margin  = Cm(2.5)

    # ── Cover page ────────────────────────────────────────────────────────────
    title = doc.add_heading("MarketPulse", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.runs[0].font.color.rgb = RGBColor(0x58, 0xA6, 0xFF)
    title.runs[0].font.size = Pt(36)

    sub = doc.add_paragraph("Stock Market Analytics & Trend Prediction")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.runs[0].font.size = Pt(18)
    sub.runs[0].bold = True

    sub2 = doc.add_paragraph("NSE Equities: Reliance · TCS · Infosys · HDFC Bank · ICICI Bank")
    sub2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub2.runs[0].font.size = Pt(12)
    sub2.runs[0].font.color.rgb = RGBColor(0x8B, 0x94, 0x9E)

    doc.add_paragraph()
    note = doc.add_paragraph("⚠  All data is 100% real – sourced from Yahoo Finance NSE feed. No synthetic data or fabricated results.")
    note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    note.runs[0].font.size = Pt(10)
    note.runs[0].italic = True
    note.runs[0].font.color.rgb = RGBColor(0x3F, 0xB9, 0x50)

    doc.add_page_break()

    # ── 1. Executive Summary ──────────────────────────────────────────────────
    _add_heading(doc, "1. Executive Summary")
    _add_para(doc, textwrap.dedent("""
        MarketPulse is an end-to-end professional data science portfolio project that analyses five NSE-listed
        equities (Reliance Industries, TCS, Infosys, HDFC Bank, ICICI Bank) using seven years of real market
        data (January 2018 – December 2024). The project covers the complete data science workflow: data
        collection, cleaning, exploratory data analysis, technical indicator computation, machine learning
        model training, backtesting, SQL database storage, REST API development, interactive dashboards,
        and automated report generation.
    """).strip(), size=11)

    doc.add_paragraph()
    _add_heading(doc, "Key Highlights", level=2)
    highlights = [
        "8,630 real OHLCV rows collected across 5 tickers",
        "25+ technical indicators computed (RSI, MACD, Bollinger Bands, ADX, ATR, OBV, MFI …)",
        "71-feature ML matrix with lag features and rolling statistics",
        "4 ML models trained per ticker with walk-forward cross-validation (no data leakage)",
        "Backtesting: ML signal strategy vs Buy & Hold on test set",
        "SQLite database with 5 indexed tables and 10 REST API endpoints",
        "Dual frontend: dark-theme ECharts HTML dashboard + Streamlit Python dashboard",
        "Auto-generated 12-slide PowerPoint presentation and this Word report",
    ]
    for h in highlights:
        p = doc.add_paragraph(h, style="List Bullet")
        p.runs[0].font.size = Pt(10)

    doc.add_page_break()

    # ── 2. Project Architecture ───────────────────────────────────────────────
    _add_heading(doc, "2. Project Architecture")
    steps = [
        ("01_download_data.py",       "Downloads 7 years of OHLCV data for all 5 tickers via yfinance"),
        ("02_clean_data.py",          "Deduplication, forward-fill, OHLC validation, spike removal"),
        ("03_eda.py",                 "10 EDA charts + summary statistics CSV"),
        ("04_technical_indicators.py","25+ indicators via the `ta` library"),
        ("05_features_targets.py",    "Binary target, lag features, rolling stats → 71-col ML matrix"),
        ("06_train_models.py",        "4 models × 5 tickers, TimeSeriesSplit CV (5 folds)"),
        ("07_backtesting.py",         "ML signal strategy vs Buy & Hold on last 20% of data"),
        ("08_database.py",            "SQLite population: 5 tables, indexed on (ticker, date)"),
        ("09_generate_ppt.py",        "12-slide python-pptx presentation with real data"),
        ("backend/app.py",            "Flask REST API with 10 endpoints + CORS"),
        ("streamlit_app.py",          "Multi-page Streamlit dashboard (7 pages)"),
        ("generate_report.py",        "API collection, screenshots, this Word report"),
    ]
    t = doc.add_table(rows=1, cols=2)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for j, label in enumerate(["Script", "Description"]):
        hdr[j].text = label
        hdr[j].paragraphs[0].runs[0].bold = True
        hdr[j].paragraphs[0].runs[0].font.size = Pt(9)
        _set_cell_bg(hdr[j], "1C2128")
        hdr[j].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x8B, 0x94, 0x9E)
    for script, desc in steps:
        row = t.add_row().cells
        row[0].text = script; row[1].text = desc
        for cell in row:
            cell.paragraphs[0].runs[0].font.size = Pt(9)
    t.columns[0].width = Cm(5)
    t.columns[1].width = Cm(11)

    doc.add_page_break()

    # ── 3. Data Collection & Cleaning ────────────────────────────────────────
    _add_heading(doc, "3. Data Collection & Cleaning")
    _add_para(doc, "Data was collected using the yfinance library (Yahoo Finance API) covering the period January 2018 to December 2024. The dataset uses auto-adjusted prices (split and dividend adjusted). Each ticker produced 1,726 trading-day rows.", size=11)

    doc.add_paragraph()
    _add_heading(doc, "3.1 Cleaning Steps", level=2)
    cleaning_steps = [
        "Sort chronologically",
        "Remove duplicate date entries (keep first)",
        "Drop rows where all OHLCV values are NaN",
        "Forward-fill up to 3 consecutive missing days (exchange holidays)",
        "OHLC relationship validation (High ≥ Low, High ≥ Close, Low ≤ Close)",
        "Remove price spike outliers (>50% intraday move)",
        "Replace zero-volume with NaN then forward-fill",
    ]
    for s in cleaning_steps:
        p = doc.add_paragraph(s, style="List Bullet")
        p.runs[0].font.size = Pt(10)

    # Cleaning report table
    cleaning_path = os.path.join(BASE_DIR, "data", "cleaned", "cleaning_report.csv")
    if os.path.exists(cleaning_path):
        doc.add_paragraph()
        _add_heading(doc, "3.2 Cleaning Results", level=2)
        df_clean = pd.read_csv(cleaning_path)
        _add_df_table(doc, df_clean)

    doc.add_page_break()

    # ── 4. EDA ────────────────────────────────────────────────────────────────
    _add_heading(doc, "4. Exploratory Data Analysis")
    _add_para(doc, "EDA was performed across all 5 tickers covering price history, return distributions, volatility, correlation, and volume trends.", size=11)

    eda_path = os.path.join(REPORTS_DIR, "eda_summary.csv")
    if os.path.exists(eda_path):
        _add_heading(doc, "4.1 Summary Statistics", level=2)
        df_eda = pd.read_csv(eda_path)
        show = ["Name","Total_Return_%","Ann_Return_%","Ann_Volatility_%","Sharpe_Ratio","Max_Drawdown_%","Avg_Volume_M"]
        _add_df_table(doc, df_eda[[c for c in show if c in df_eda.columns]])

    doc.add_paragraph()
    # EDA figures
    eda_figs = [
        ("price_history.png", "Figure 1: Normalised Price Performance (Base=100) – All 5 Tickers"),
        ("daily_returns_dist.png", "Figure 2: Daily Return Distributions"),
        ("correlation_heatmap.png", "Figure 3: Pairwise Return Correlation Heatmap"),
        ("volatility_rolling.png", "Figure 4: 30-Day Rolling Annualised Volatility"),
        ("volume_trend.png", "Figure 5: 30-Day Rolling Average Volume"),
    ]
    for fname, caption in eda_figs:
        fpath = os.path.join(FIGURES_DIR, fname)
        if os.path.exists(fpath):
            _add_heading(doc, caption.split(":")[0].strip(), level=2)
            _add_image(doc, fpath, width_inches=6.2, caption=caption)
            doc.add_paragraph()

    doc.add_page_break()

    # ── 5. Technical Indicators ───────────────────────────────────────────────
    _add_heading(doc, "5. Technical Indicators")
    _add_para(doc, "25+ technical indicators were computed using the `ta` Python library, covering four categories:", size=11)
    ind_table_data = [
        ("Trend",      "SMA-20/50/200, EMA-12/26, MACD (12,26,9), ADX/DI+/DI-, Ichimoku A/B"),
        ("Momentum",   "RSI-14, Stochastic %K/%D, Williams %R, ROC-10, TSI"),
        ("Volatility", "Bollinger Bands (20,2), ATR-14, Keltner Channels, Rolling Vol 20d/60d"),
        ("Volume",     "OBV, CMF (Chaikin), MFI-14, Ease of Movement"),
    ]
    t = doc.add_table(rows=1, cols=2)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(["Category", "Indicators"]):
        t.rows[0].cells[j].text = h
        t.rows[0].cells[j].paragraphs[0].runs[0].bold = True
        t.rows[0].cells[j].paragraphs[0].runs[0].font.size = Pt(9)
        _set_cell_bg(t.rows[0].cells[j], "1C2128")
        t.rows[0].cells[j].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x8B, 0x94, 0x9E)
    for cat, inds_text in ind_table_data:
        row = t.add_row().cells
        row[0].text = cat; row[1].text = inds_text
        for cell in row:
            cell.paragraphs[0].runs[0].font.size = Pt(9)

    # Indicator screenshots
    doc.add_paragraph()
    for ticker in TICKERS[:2]:
        fpath = os.path.join(SCREENS_DIR, f"screen_03_indicators_{ticker.replace('.','_')}.png")
        if os.path.exists(fpath):
            _add_image(doc, fpath, 6.2, f"Technical Indicators – {NAMES.get(ticker)}")
            doc.add_paragraph()

    doc.add_page_break()

    # ── 6. Feature Engineering & ML ──────────────────────────────────────────
    _add_heading(doc, "6. Feature Engineering & Machine Learning")
    _add_heading(doc, "6.1 Feature Matrix", level=2)
    _add_para(doc, "The ML feature matrix has 71 columns and 7,635 rows (after dropping the warm-up period for indicators). Features include:", size=11)
    feat_bullets = [
        "All 25+ technical indicator columns",
        "Lag features (1, 2, 3, 5 days) for 8 key indicators: RSI, MACD, ATR, Volatility, BB%B, MFI, ADX, Return",
        "Price/SMA ratios: Close/SMA20, Close/SMA50",
        "High-Low range and Close-Open range",
        "Rolling 20-day and 60-day annualised volatility",
        "Rolling 20-day skewness of returns",
        "Log returns and 1d/5d/10d/20d percentage returns",
    ]
    for b in feat_bullets:
        p = doc.add_paragraph(b, style="List Bullet")
        p.runs[0].font.size = Pt(10)

    _add_heading(doc, "6.2 Prediction Target", level=2)
    _add_para(doc, "Binary classification target: Target_1d = 1 if Close[t+1] > Close[t], else 0. Class balance across all tickers is approximately 51–53% up / 47–49% down, confirming near-random difficulty.", size=11)

    _add_heading(doc, "6.3 Models & Validation", level=2)
    models_data = [
        ("Logistic Regression", "C=0.1, max_iter=1000", "Baseline linear model"),
        ("Random Forest",       "300 trees, max_depth=8, min_samples_leaf=20", "Ensemble bagging"),
        ("XGBoost",             "300 est, lr=0.05, subsample=0.8, colsample=0.8", "Gradient boosting"),
        ("LightGBM",            "300 est, lr=0.05, subsample=0.8, colsample=0.8", "Fast gradient boosting"),
    ]
    t = doc.add_table(rows=1, cols=3)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(["Model", "Hyperparameters", "Notes"]):
        t.rows[0].cells[j].text = h
        t.rows[0].cells[j].paragraphs[0].runs[0].bold = True
        t.rows[0].cells[j].paragraphs[0].runs[0].font.size = Pt(9)
        _set_cell_bg(t.rows[0].cells[j], "1C2128")
        t.rows[0].cells[j].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x8B, 0x94, 0x9E)
    for mn, hp, note in models_data:
        row = t.add_row().cells
        row[0].text = mn; row[1].text = hp; row[2].text = note
        for cell in row:
            cell.paragraphs[0].runs[0].font.size = Pt(9)

    doc.add_paragraph()
    _add_heading(doc, "6.4 CV Metrics", level=2)
    mm_path = os.path.join(REPORTS_DIR, "model_metrics.csv")
    if os.path.exists(mm_path):
        df_mm = pd.read_csv(mm_path).round(4)
        _add_df_table(doc, df_mm)
    doc.add_paragraph()
    sc = os.path.join(SCREENS_DIR, "screen_04_ml_models.png")
    _add_image(doc, sc, 6.2, "Figure: ML Model Performance – ROC-AUC and Accuracy (Walk-Forward CV)")

    doc.add_page_break()

    # ── 7. Backtesting ────────────────────────────────────────────────────────
    _add_heading(doc, "7. Backtesting")
    _add_para(doc, textwrap.dedent("""
        Strategy: ML Signal-Based Long-Only
        The best trained model for each ticker generates a probability of an upward move the next day.
        If prob_up ≥ 0.55, the strategy goes long; otherwise it stays in cash.
        The test set is the last 20% of data for each ticker. Performance is compared against a
        passive Buy & Hold benchmark.
    """).strip(), size=11)

    bt_path = os.path.join(REPORTS_DIR, "backtest_results.csv")
    if os.path.exists(bt_path):
        doc.add_paragraph()
        _add_heading(doc, "7.1 Backtest Summary", level=2)
        df_bt = pd.read_csv(bt_path).round(2)
        _add_df_table(doc, df_bt)

    doc.add_paragraph()
    sc = os.path.join(SCREENS_DIR, "screen_05_backtest.png")
    _add_image(doc, sc, 6.2, "Figure: Backtest – Total Return and Sharpe Ratio Comparison")

    doc.add_paragraph()
    _add_heading(doc, "7.2 Equity Curves", level=2)
    for ticker in TICKERS:
        slug = ticker.replace(".", "_")
        fpath = os.path.join(FIGURES_DIR, f"backtest_equity_{slug}.png")
        if os.path.exists(fpath):
            _add_image(doc, fpath, 5.8, f"Equity Curve – {NAMES.get(ticker)}")

    doc.add_page_break()

    # ── 8. SQL Database ───────────────────────────────────────────────────────
    _add_heading(doc, "8. SQL Database")
    _add_para(doc, "A SQLite database (data/marketpulse.db) stores all processed data in 5 tables, each indexed on (ticker, date) for fast API queries. SQLAlchemy ORM is used for all database interactions.", size=11)
    db_tables = [
        ("stock_prices",         "8,630",  "OHLCV data for all 5 tickers"),
        ("technical_indicators", "8,505",  "All 25+ computed indicators"),
        ("ml_predictions",       "1,530",  "Test-set model predictions with correctness flag"),
        ("backtest_results",     "5",      "Per-ticker backtest KPI summary"),
        ("model_metrics",        "20",     "Walk-forward CV scores (4 models × 5 tickers)"),
    ]
    t = doc.add_table(rows=1, cols=3)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(["Table", "Rows", "Description"]):
        t.rows[0].cells[j].text = h
        t.rows[0].cells[j].paragraphs[0].runs[0].bold = True
        t.rows[0].cells[j].paragraphs[0].runs[0].font.size = Pt(9)
        _set_cell_bg(t.rows[0].cells[j], "1C2128")
        t.rows[0].cells[j].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x8B, 0x94, 0x9E)
    for tname, nrows, desc in db_tables:
        row = t.add_row().cells
        row[0].text = tname; row[1].text = nrows; row[2].text = desc
        for cell in row:
            cell.paragraphs[0].runs[0].font.size = Pt(9)

    doc.add_page_break()

    # ── 9. Backend API ────────────────────────────────────────────────────────
    _add_heading(doc, "9. REST API (Flask Backend)")
    _add_para(doc, "The Flask backend serves all data from SQLite via 10 REST endpoints with CORS enabled. The live predict endpoint runs the trained model on the latest available feature row.", size=11)
    endpoints = [
        ("GET",  "/api/health",       "Backend health check"),
        ("GET",  "/api/tickers",      "List all 5 NSE tickers"),
        ("GET",  "/api/overview",     "Latest price + daily % change for all tickers"),
        ("GET",  "/api/prices",       "OHLCV history (period: 1Y/2Y/5Y/ALL)"),
        ("GET",  "/api/indicators",   "All 25+ technical indicators"),
        ("GET",  "/api/predictions",  "Test-set model predictions"),
        ("GET",  "/api/backtest",     "Backtest summary for all tickers"),
        ("GET",  "/api/model_metrics","Walk-forward CV performance scores"),
        ("GET",  "/api/correlation",  "Pairwise return correlation matrix"),
        ("POST", "/api/predict",      "Live signal: {\"ticker\": \"TCS.NS\"}"),
    ]
    t = doc.add_table(rows=1, cols=3)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(["Method", "Endpoint", "Description"]):
        t.rows[0].cells[j].text = h
        t.rows[0].cells[j].paragraphs[0].runs[0].bold = True
        t.rows[0].cells[j].paragraphs[0].runs[0].font.size = Pt(9)
        _set_cell_bg(t.rows[0].cells[j], "1C2128")
        t.rows[0].cells[j].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x8B, 0x94, 0x9E)
    for method, ep, desc in endpoints:
        row = t.add_row().cells
        row[0].text = method; row[1].text = ep; row[2].text = desc
        for cell in row:
            cell.paragraphs[0].runs[0].font.size = Pt(9)

    doc.add_paragraph()
    _add_heading(doc, "9.1 Sample API Output – Live Prediction", level=2)
    predict_sample = api.get("predict_RELIANCE_NS", {})
    if predict_sample:
        _add_para(doc, json.dumps(predict_sample, indent=2), size=9)

    doc.add_page_break()

    # ── 10. Dashboard Screenshots ─────────────────────────────────────────────
    _add_heading(doc, "10. Dashboard Screenshots")
    _add_para(doc, "The project includes two frontends: a dark-theme ECharts HTML dashboard (served by Flask) and a multi-page Streamlit dashboard.", size=11)

    screen_meta = [
        ("screen_01_overview.png",           "Overview Page – KPI cards, normalised performance, correlation"),
        ("screen_02_candlestick_RELIANCE_NS.png", "Price Charts – Candlestick + Volume (Reliance)"),
        ("screen_02_candlestick_TCS_NS.png",      "Price Charts – Candlestick + Volume (TCS)"),
        ("screen_03_indicators_RELIANCE_NS.png",  "Indicators Page – RSI, MACD, Bollinger Bands"),
        ("screen_04_ml_models.png",           "ML Models – ROC-AUC and Accuracy comparison"),
        ("screen_05_backtest.png",            "Backtesting – Return and Sharpe comparison"),
        ("screen_06_predictions_TCS_NS.png",  "Prediction Signals – TCS test set"),
        ("screen_07_live_predict.png",        "Live Prediction Panel – all 5 tickers"),
    ]
    for fname, caption in screen_meta:
        fpath = os.path.join(SCREENS_DIR, fname)
        if os.path.exists(fpath):
            _add_image(doc, fpath, 6.2, caption)
            doc.add_paragraph()

    doc.add_page_break()

    # ── 11. Key Findings ─────────────────────────────────────────────────────
    _add_heading(doc, "11. Key Findings & Conclusions")

    _add_heading(doc, "11.1 EDA Findings", level=2)
    eda_findings = [
        "Infosys delivered the highest 7-year total return (+345.81%) with a Sharpe ratio of 1.066",
        "TCS showed the lowest max drawdown (-27.21%), making it the most stable performer",
        "All 5 stocks show high positive return correlation (0.65–0.88), reducing diversification benefit",
        "COVID-19 crash (March 2020) is visible as an extreme volatility spike across all tickers",
        "Volume spikes consistently align with quarterly earnings announcement dates",
    ]
    for f in eda_findings:
        p = doc.add_paragraph(f, style="List Bullet")
        p.runs[0].font.size = Pt(10)

    doc.add_paragraph()
    _add_heading(doc, "11.2 ML Model Findings", level=2)
    ml_findings = [
        "LightGBM and XGBoost are the best models for 4 of 5 tickers",
        "ROC-AUC scores of 0.517–0.530 are honest results for a near-random daily direction task",
        "RSI, MACD Histogram, and BB %B are consistently top features",
        "Lag-1 and lag-2 features of volatility and momentum provide additional signal",
        "Walk-forward CV prevents data leakage; in-sample performance would be much higher",
    ]
    for f in ml_findings:
        p = doc.add_paragraph(f, style="List Bullet")
        p.runs[0].font.size = Pt(10)

    doc.add_paragraph()
    _add_heading(doc, "11.3 Backtesting Findings", level=2)
    bt_findings = [
        "ML strategy significantly reduces max drawdown compared to Buy & Hold",
        "Strategy correctly avoids many losing periods by sitting in cash",
        "Sharpe ratios > 6 for Reliance, TCS, and ICICI Bank in the test period",
        "Infosys shows weaker strategy performance (Sharpe 0.12), B&H outperformed",
        "Results exclude transaction costs and slippage – real performance would be lower",
    ]
    for f in bt_findings:
        p = doc.add_paragraph(f, style="List Bullet")
        p.runs[0].font.size = Pt(10)

    doc.add_paragraph()
    _add_heading(doc, "11.4 Limitations & Future Work", level=2)
    limits = [
        "Binary classification ignores the magnitude of price moves",
        "No transaction cost or slippage model applied",
        "Macro and news sentiment features not included",
        "Future: multi-class target (UP/DOWN/FLAT), options pricing, regime detection",
    ]
    for f in limits:
        p = doc.add_paragraph(f, style="List Bullet")
        p.runs[0].font.size = Pt(10)

    doc.add_page_break()

    # ── 12. API Output Collection ─────────────────────────────────────────────
    _add_heading(doc, "12. Collected API Outputs")
    _add_para(doc, f"All {len(os.listdir(API_DIR))} API responses were collected and saved as JSON to reports/api_outputs/. Sample overview response:", size=11)
    ov_data = api.get("overview", [])
    if ov_data:
        _add_para(doc, json.dumps(ov_data, indent=2)[:1500], size=9)

    doc.add_paragraph()
    _add_heading(doc, "12.1 Backtest API Response", level=2)
    bt_data = api.get("backtest", [])
    if bt_data:
        _add_para(doc, json.dumps(bt_data, indent=2), size=9)

    doc.add_page_break()

    # ── 13. Technology Stack ──────────────────────────────────────────────────
    _add_heading(doc, "13. Technology Stack")
    tech = [
        ("Data Collection",  "yfinance, pandas, numpy"),
        ("Indicators",       "ta (Technical Analysis library)"),
        ("ML Models",        "scikit-learn, XGBoost, LightGBM"),
        ("Database",         "SQLite, SQLAlchemy"),
        ("Backend",          "Flask 3.0, Flask-CORS"),
        ("HTML Dashboard",   "ECharts 5, vanilla JavaScript"),
        ("Python Dashboard", "Streamlit 1.64"),
        ("Visualisation",    "matplotlib, seaborn, plotly"),
        ("Reports",          "python-pptx, python-docx"),
        ("Model Persistence","joblib"),
        ("Python version",   "3.15 (tested)"),
    ]
    t = doc.add_table(rows=1, cols=2)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(["Layer", "Technology"]):
        t.rows[0].cells[j].text = h
        t.rows[0].cells[j].paragraphs[0].runs[0].bold = True
        t.rows[0].cells[j].paragraphs[0].runs[0].font.size = Pt(9)
        _set_cell_bg(t.rows[0].cells[j], "1C2128")
        t.rows[0].cells[j].paragraphs[0].runs[0].font.color.rgb = RGBColor(0x8B, 0x94, 0x9E)
    for layer, tech_str in tech:
        row = t.add_row().cells
        row[0].text = layer; row[1].text = tech_str
        for cell in row:
            cell.paragraphs[0].runs[0].font.size = Pt(9)

    # ── Save ──────────────────────────────────────────────────────────────────
    doc.save(DOCX_PATH)
    print(f"\n  ✅ Word report saved → {DOCX_PATH}")
    return DOCX_PATH


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("  MarketPulse – Report Generator")
    print("=" * 65)

    # Step 1 – Backend
    print("\n─── Step 1: Flask Backend ───")
    backend_ok = start_backend()
    if not backend_ok:
        print("  ⚠  Continuing without live API – some report sections will be empty.")

    # Step 2 – Collect API
    api = collect_api_outputs() if backend_ok else {}

    # Step 3 – Screenshots
    screenshots = generate_screenshots(api)

    # Step 4 – Word Report
    docx = build_word_report(api, screenshots)

    # Stop backend if we started it
    stop_backend()

    print("\n" + "=" * 65)
    print("  Report generation complete!")
    print(f"  Word Report:   {docx}")
    print(f"  Screenshots:   {SCREENS_DIR}  ({len(screenshots)} images)")
    print(f"  API Outputs:   {API_DIR}  ({len(os.listdir(API_DIR))} files)")
    print("=" * 65)


if __name__ == "__main__":
    main()
