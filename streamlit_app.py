"""
MarketPulse – Streamlit Dashboard
Full multi-page analytics UI calling the Flask REST API.
Run:  streamlit run streamlit_app.py
"""

import os
import time
import requests
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import streamlit as st


# ── pyarrow-free table renderer ───────────────────────────────────────────────
def show_table(df: pd.DataFrame):
    """Render a DataFrame as HTML – avoids st.dataframe which needs pyarrow."""
    html = (
        df.to_html(index=False, border=0, classes="mp-table")
          .replace("<th>", '<th style="'
                   'background:#1c2128;color:#8b949e;font-size:11px;'
                   'text-transform:uppercase;letter-spacing:.6px;'
                   'padding:8px 12px;border-bottom:1px solid #30363d;">')
          .replace("<td>", '<td style="'
                   'padding:7px 12px;font-size:12px;color:#e6edf3;'
                   'border-bottom:1px solid #21262d;">')
          .replace("<tr>", '<tr style="background:#0d1117;">')
    )
    st.markdown(
        f'<div style="overflow-x:auto;border:1px solid #30363d;'
        f'border-radius:6px;margin-bottom:8px">{html}</div>',
        unsafe_allow_html=True,
    )

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE = "http://localhost:5000/api"
FIGURES_DIR = os.path.join(os.path.dirname(__file__), "reports", "figures")

TICKERS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
NAMES   = {
    "RELIANCE.NS": "Reliance", "TCS.NS": "TCS",
    "INFY.NS": "Infosys", "HDFCBANK.NS": "HDFC Bank", "ICICIBANK.NS": "ICICI Bank",
}
COLORS = ["#2196F3", "#F44336", "#4CAF50", "#FF9800", "#9C27B0"]
DARK   = "#0d1117"
SURF   = "#161b22"

st.set_page_config(
    page_title="MarketPulse – NSE Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#0d1117}
[data-testid="stSidebar"]{background:#161b22}
[data-testid="stHeader"]{background:#0d1117}
.stMetric{background:#1c2128;border:1px solid #30363d;border-radius:8px;padding:12px}
.stMetric label{color:#8b949e !important;font-size:11px !important}
div[data-testid="metric-container"] > div:first-child label {color:#8b949e !important}
h1,h2,h3{color:#e6edf3}
.stDataFrame{border:1px solid #30363d;border-radius:6px}
</style>
""", unsafe_allow_html=True)

# ── API helpers ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def api_get(endpoint: str, params: dict = None):
    try:
        r = requests.get(f"{API_BASE}/{endpoint}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error ({endpoint}): {e}")
        return None


def api_post(endpoint: str, payload: dict):
    try:
        r = requests.post(f"{API_BASE}/{endpoint}", json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error ({endpoint}): {e}")
        return None


def backend_alive() -> bool:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=3)
        return r.ok
    except Exception:
        return False


# ── Matplotlib figure helpers ─────────────────────────────────────────────────
def fig_price_history(prices_all: dict) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(11, 4), facecolor=DARK)
    ax.set_facecolor(DARK)
    for i, (ticker, prices) in enumerate(prices_all.items()):
        if not prices: continue
        df = pd.DataFrame(prices)
        df["date"] = pd.to_datetime(df["date"])
        norm = df["close"] / df["close"].iloc[0] * 100
        ax.plot(df["date"], norm, color=COLORS[i], label=NAMES[ticker], lw=1.8)
    ax.set_title("Normalised Price Performance (Base = 100)", color="#e6edf3", fontsize=13, fontweight="bold")
    ax.set_xlabel("Date", color="#8b949e"); ax.set_ylabel("Index", color="#8b949e")
    ax.tick_params(colors="#8b949e"); ax.legend(facecolor=SURF, labelcolor="#e6edf3", fontsize=9)
    for spine in ax.spines.values(): spine.set_edgecolor("#30363d")
    ax.grid(alpha=0.15, color="#30363d")
    fig.tight_layout()
    return fig


def fig_candlestick(prices: list, ticker: str) -> plt.Figure:
    df = pd.DataFrame(prices[-90:]).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(11, 4), facecolor=DARK)
    ax.set_facecolor(DARK)
    for i, row in df.iterrows():
        col = "#26A69A" if row["close"] >= row["open"] else "#EF5350"
        ax.plot([i, i], [row["low"], row["high"]], color=col, lw=1)
        ax.bar(i, abs(row["close"] - row["open"]),
               bottom=min(row["open"], row["close"]),
               color=col, width=0.6, alpha=0.92)
    ticks = range(0, len(df), 10)
    ax.set_xticks(list(ticks))
    ax.set_xticklabels([df["date"].iloc[t][:10] for t in ticks], rotation=25, color="#8b949e", fontsize=8)
    ax.set_title(f"{NAMES.get(ticker, ticker)} – Last 90 Trading Days", color="#e6edf3", fontsize=12, fontweight="bold")
    ax.set_ylabel("Price (₹)", color="#8b949e"); ax.tick_params(colors="#8b949e")
    for spine in ax.spines.values(): spine.set_edgecolor("#30363d")
    ax.grid(alpha=0.12, axis="y", color="#30363d")
    g = mpatches.Patch(color="#26A69A", label="Bullish")
    r = mpatches.Patch(color="#EF5350", label="Bearish")
    ax.legend(handles=[g, r], facecolor=SURF, labelcolor="#e6edf3", fontsize=9)
    fig.tight_layout()
    return fig


def fig_rsi(inds: list, ticker: str) -> plt.Figure:
    df = pd.DataFrame(inds)
    df["date"] = pd.to_datetime(df["date"])
    fig, ax = plt.subplots(figsize=(11, 3), facecolor=DARK)
    ax.set_facecolor(DARK)
    ax.plot(df["date"], df["rsi_14"], color="#bc8cff", lw=1.5, label="RSI-14")
    ax.axhline(70, color="#f85149", ls="--", lw=1, label="Overbought (70)")
    ax.axhline(30, color="#3fb950", ls="--", lw=1, label="Oversold (30)")
    ax.fill_between(df["date"], df["rsi_14"], 70, where=df["rsi_14"] >= 70, alpha=0.15, color="#f85149")
    ax.fill_between(df["date"], df["rsi_14"], 30, where=df["rsi_14"] <= 30, alpha=0.15, color="#3fb950")
    ax.set_ylim(0, 100)
    ax.set_title(f"{NAMES.get(ticker, ticker)} – RSI-14", color="#e6edf3", fontsize=12, fontweight="bold")
    ax.tick_params(colors="#8b949e"); ax.legend(facecolor=SURF, labelcolor="#e6edf3", fontsize=9)
    for spine in ax.spines.values(): spine.set_edgecolor("#30363d")
    ax.grid(alpha=0.12, color="#30363d"); fig.tight_layout()
    return fig


def fig_macd(inds: list, ticker: str) -> plt.Figure:
    df = pd.DataFrame(inds)
    df["date"] = pd.to_datetime(df["date"])
    fig, ax = plt.subplots(figsize=(11, 3), facecolor=DARK)
    ax.set_facecolor(DARK)
    ax.plot(df["date"], df["macd"], color="#58a6ff", lw=1.5, label="MACD")
    ax.plot(df["date"], df["macd_signal"], color="#ffa657", lw=1.5, label="Signal")
    colors_hist = ["#3fb950" if v >= 0 else "#f85149" for v in df["macd_hist"]]
    ax.bar(df["date"], df["macd_hist"], color=colors_hist, width=1, alpha=0.7, label="Histogram")
    ax.set_title(f"{NAMES.get(ticker, ticker)} – MACD (12,26,9)", color="#e6edf3", fontsize=12, fontweight="bold")
    ax.tick_params(colors="#8b949e"); ax.legend(facecolor=SURF, labelcolor="#e6edf3", fontsize=9)
    for spine in ax.spines.values(): spine.set_edgecolor("#30363d")
    ax.grid(alpha=0.12, color="#30363d"); fig.tight_layout()
    return fig


def fig_bollinger(prices: list, inds: list, ticker: str) -> plt.Figure:
    df_p = pd.DataFrame(prices)
    df_p["date"] = pd.to_datetime(df_p["date"])
    df_i = pd.DataFrame(inds)
    df_i["date"] = pd.to_datetime(df_i["date"])
    merged = pd.merge(df_p[["date","close"]], df_i[["date","bb_upper","bb_lower"]], on="date")
    fig, ax = plt.subplots(figsize=(11, 4), facecolor=DARK)
    ax.set_facecolor(DARK)
    ax.plot(merged["date"], merged["close"], color="#ffa657", lw=1.8, label="Close")
    ax.plot(merged["date"], merged["bb_upper"], color="#58a6ff", lw=1, ls="--", label="Upper Band")
    ax.plot(merged["date"], merged["bb_lower"], color="#58a6ff", lw=1, ls="--", label="Lower Band")
    ax.fill_between(merged["date"], merged["bb_upper"], merged["bb_lower"], alpha=0.06, color="#58a6ff")
    ax.set_title(f"{NAMES.get(ticker, ticker)} – Bollinger Bands (20,2)", color="#e6edf3", fontsize=12, fontweight="bold")
    ax.tick_params(colors="#8b949e"); ax.legend(facecolor=SURF, labelcolor="#e6edf3", fontsize=9)
    for spine in ax.spines.values(): spine.set_edgecolor("#30363d")
    ax.grid(alpha=0.12, color="#30363d"); fig.tight_layout()
    return fig


def fig_model_metrics(metrics: list) -> plt.Figure:
    df = pd.DataFrame(metrics)
    model_names = df["model"].unique()
    tickers_short = [NAMES.get(t, t) for t in df["ticker"].unique()]
    x = np.arange(len(tickers_short)); w = 0.2
    fig, axes = plt.subplots(1, 2, figsize=(13, 4), facecolor=DARK)
    col_map = {"LogisticRegression": "#58a6ff", "RandomForest": "#3fb950",
               "XGBoost": "#ffa657", "LightGBM": "#bc8cff"}
    for ax, metric, title in zip(axes, ["roc_auc", "accuracy"],
                                  ["ROC-AUC Score", "Accuracy"]):
        ax.set_facecolor(DARK)
        for j, mn in enumerate(model_names):
            sub = df[df["model"] == mn]
            vals = [sub[sub["ticker"] == t][metric].values[0] if len(sub[sub["ticker"] == t]) else 0
                    for t in df["ticker"].unique()]
            ax.bar(x + j*w, vals, w, label=mn, color=col_map.get(mn, COLORS[j]), alpha=0.85)
        ax.set_xticks(x + w*1.5)
        ax.set_xticklabels(tickers_short, rotation=15, color="#8b949e", fontsize=9)
        ax.set_title(title, color="#e6edf3", fontsize=11, fontweight="bold")
        ax.tick_params(colors="#8b949e"); ax.set_ylim(0.45, 0.6)
        for spine in ax.spines.values(): spine.set_edgecolor("#30363d")
        ax.grid(alpha=0.12, axis="y", color="#30363d")
        ax.legend(facecolor=SURF, labelcolor="#e6edf3", fontsize=8)
    fig.suptitle("ML Model Performance – Walk-Forward CV (5 Folds)", color="#e6edf3", fontsize=13, fontweight="bold")
    fig.tight_layout(); return fig


def fig_backtest(bt: list) -> plt.Figure:
    df = pd.DataFrame(bt)
    names = [NAMES.get(t, t) for t in df["ticker"]]
    x = np.arange(len(names)); w = 0.35
    fig, axes = plt.subplots(1, 2, figsize=(13, 4), facecolor=DARK)

    # Return comparison
    ax = axes[0]; ax.set_facecolor(DARK)
    strat_ret = pd.to_numeric(df["strat_total_return_%"], errors="coerce").fillna(0)
    bnh_ret   = pd.to_numeric(df["bnh_total_return_%"],   errors="coerce").fillna(0)
    ax.bar(x - w/2, strat_ret, w, label="ML Strategy", color="#58a6ff", alpha=0.85)
    ax.bar(x + w/2, bnh_ret,   w, label="Buy & Hold",  color="#8b949e", alpha=0.85)
    ax.set_xticks(x); ax.set_xticklabels(names, color="#8b949e", fontsize=9)
    ax.set_title("Total Return % (Test Set)", color="#e6edf3", fontsize=11, fontweight="bold")
    ax.tick_params(colors="#8b949e"); ax.legend(facecolor=SURF, labelcolor="#e6edf3", fontsize=9)
    for spine in ax.spines.values(): spine.set_edgecolor("#30363d")
    ax.grid(alpha=0.12, axis="y", color="#30363d")

    # Sharpe + MaxDD
    ax2 = axes[1]; ax2.set_facecolor(DARK)
    sharpe = pd.to_numeric(df["strat_sharpe"], errors="coerce").fillna(0)
    colors_s = ["#3fb950" if v >= 1 else "#ffa657" for v in sharpe]
    ax2.bar(x, sharpe, color=colors_s, alpha=0.85)
    ax2.set_xticks(x); ax2.set_xticklabels(names, color="#8b949e", fontsize=9)
    ax2.set_title("Sharpe Ratio – ML Strategy", color="#e6edf3", fontsize=11, fontweight="bold")
    ax2.tick_params(colors="#8b949e")
    for spine in ax2.spines.values(): spine.set_edgecolor("#30363d")
    ax2.grid(alpha=0.12, axis="y", color="#30363d")

    fig.suptitle("Backtesting Results – ML Strategy vs Buy & Hold", color="#e6edf3", fontsize=13, fontweight="bold")
    fig.tight_layout(); return fig


def fig_correlation(corr_data: dict) -> plt.Figure:
    tickers_short = [NAMES.get(t, t) for t in corr_data["tickers"]]
    mat = np.array(corr_data["matrix"])
    fig, ax = plt.subplots(figsize=(7, 6), facecolor=DARK)
    ax.set_facecolor(DARK)
    im = ax.imshow(mat, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(tickers_short))); ax.set_yticks(range(len(tickers_short)))
    ax.set_xticklabels(tickers_short, rotation=20, ha="right", color="#8b949e", fontsize=10)
    ax.set_yticklabels(tickers_short, color="#8b949e", fontsize=10)
    for i in range(len(mat)):
        for j in range(len(mat)):
            ax.text(j, i, f"{mat[i,j]:.2f}", ha="center", va="center",
                    color="#0d1117" if abs(mat[i,j]) > 0.5 else "#e6edf3", fontsize=10, fontweight="bold")
    plt.colorbar(im, ax=ax)
    ax.set_title("Return Correlation Matrix (2018–2024)", color="#e6edf3", fontsize=12, fontweight="bold")
    for spine in ax.spines.values(): spine.set_edgecolor("#30363d")
    fig.tight_layout(); return fig


def fig_prediction_signals(preds: list, ticker: str) -> plt.Figure:
    df = pd.DataFrame(preds)
    df["date"] = pd.to_datetime(df["date"])
    buy  = df[df["predicted_up"] == 1]
    sell = df[df["predicted_up"] == 0]
    fig, axes = plt.subplots(2, 1, figsize=(12, 6), facecolor=DARK, sharex=True)
    # Price + signals
    ax = axes[0]; ax.set_facecolor(DARK)
    ax.plot(df["date"], df["close"], color="#ffa657", lw=1.5, label="Close")
    ax.scatter(buy["date"],  buy["close"],  color="#3fb950", s=12, label="Buy Signal",  zorder=5, alpha=0.8)
    ax.scatter(sell["date"], sell["close"], color="#f85149", s=12, label="Hold Signal", zorder=5, alpha=0.6)
    ax.set_title(f"{NAMES.get(ticker, ticker)} – ML Prediction Signals (Test Set)", color="#e6edf3", fontsize=12, fontweight="bold")
    ax.tick_params(colors="#8b949e"); ax.legend(facecolor=SURF, labelcolor="#e6edf3", fontsize=9)
    for spine in ax.spines.values(): spine.set_edgecolor("#30363d")
    ax.grid(alpha=0.12, color="#30363d")
    # Rolling accuracy
    ax2 = axes[1]; ax2.set_facecolor(DARK)
    window = 20
    rolling = [df["correct"].iloc[max(0,i-window):i].mean()*100 for i in range(1, len(df)+1)]
    ax2.plot(df["date"], rolling, color="#58a6ff", lw=1.5, label=f"{window}d Rolling Acc%")
    ax2.axhline(50, color="#8b949e", ls="--", lw=1)
    ax2.set_ylabel("Accuracy %", color="#8b949e"); ax2.set_ylim(25, 80)
    ax2.tick_params(colors="#8b949e"); ax2.legend(facecolor=SURF, labelcolor="#e6edf3", fontsize=9)
    for spine in ax2.spines.values(): spine.set_edgecolor("#30363d")
    ax2.grid(alpha=0.12, color="#30363d")
    fig.tight_layout(); return fig


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 MarketPulse")
    st.caption("NSE Stock Analytics & ML Signals")
    st.divider()

    alive = backend_alive()
    if alive:
        st.success("🟢 Backend Online", icon="✅")
    else:
        st.error("🔴 Backend Offline – start `python backend/app.py`")

    page = st.radio(
        "Navigate",
        ["🏠 Overview", "📊 Price Charts", "📉 Indicators",
         "🔍 EDA", "🤖 ML Models", "⏳ Backtesting", "🎯 Live Predict"],
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown("**Select Stock**")
    active_ticker = st.selectbox(
        "Ticker",
        TICKERS,
        format_func=lambda t: f"{NAMES[t]} ({t})",
        label_visibility="collapsed"
    )

    st.divider()
    ov_data = api_get("overview") or []
    if ov_data:
        st.markdown("**Market Snapshot**")
        for item in ov_data:
            chg = item.get("change_pct", 0)
            arrow = "▲" if chg >= 0 else "▼"
            color = "green" if chg >= 0 else "red"
            st.markdown(
                f"`{NAMES.get(item['ticker'], item['ticker'])}` "
                f"₹{item['close']:,.2f}  "
                f":{color}[{arrow} {chg:+.2f}%]",
                unsafe_allow_html=False
            )

    st.divider()
    st.caption("Data: NSE via yfinance\nModels: LightGBM · XGBoost · RF · LR")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if "Overview" in page:
    st.title("📈 Market Overview")
    st.caption("NSE-listed equities: 2018–2024  |  Real data via Yahoo Finance")

    # KPI row
    ov = api_get("overview") or []
    if ov:
        cols = st.columns(5)
        for col, item in zip(cols, ov):
            chg = item.get("change_pct", 0)
            col.metric(
                label=item["name"],
                value=f"₹{item['close']:,.2f}",
                delta=f"{chg:+.2f}%",
            )

    st.divider()

    # Normalised price chart
    st.subheader("Normalised Price Performance (Base = 100)")
    prices_all = {t: api_get("prices", {"ticker": t, "period": "ALL"}) for t in TICKERS}
    fig = fig_price_history(prices_all)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Return Correlation Matrix")
        corr = api_get("correlation")
        if corr:
            fig2 = fig_correlation(corr)
            st.pyplot(fig2, use_container_width=True)
            plt.close(fig2)

    with col2:
        st.subheader("EDA Summary Statistics")
        eda_path = os.path.join("reports", "eda_summary.csv")
        if os.path.exists(eda_path):
            eda_df = pd.read_csv(eda_path)
            show_cols = ["Name", "Total_Return_%", "Ann_Return_%",
                         "Ann_Volatility_%", "Sharpe_Ratio", "Max_Drawdown_%"]
            disp = eda_df[show_cols].copy()
            for c in show_cols:
                if c != "Name":
                    disp[c] = disp[c].apply(lambda v: f"{v:.2f}" if pd.notna(v) else "")
            show_table(disp)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PRICE CHARTS
# ══════════════════════════════════════════════════════════════════════════════
elif "Price Charts" in page:
    st.title(f"📊 Price Charts – {NAMES.get(active_ticker)}")
    period_map = {"1 Year": "1Y", "2 Years": "2Y", "5 Years": "5Y", "All": "ALL"}
    period_label = st.radio("Period", list(period_map.keys()), index=1, horizontal=True)
    period = period_map[period_label]

    prices = api_get("prices", {"ticker": active_ticker, "period": period})
    if prices:
        df_p = pd.DataFrame(prices)
        df_p["date"] = pd.to_datetime(df_p["date"])

        st.subheader(f"Candlestick Chart ({period_label})")
        fig = fig_candlestick(prices, active_ticker)
        st.pyplot(fig, use_container_width=True); plt.close(fig)

        st.subheader("Volume")
        fig_v, ax_v = plt.subplots(figsize=(11, 2.5), facecolor=DARK)
        ax_v.set_facecolor(DARK)
        bar_colors = ["#3fb95080" if r["close"] >= r["open"] else "#f8514980" for r in prices]
        ax_v.bar(range(len(df_p)), df_p["volume"] / 1e6, color=bar_colors, width=0.8)
        ax_v.set_ylabel("Volume (M)", color="#8b949e"); ax_v.tick_params(colors="#8b949e")
        for spine in ax_v.spines.values(): spine.set_edgecolor("#30363d")
        ax_v.grid(alpha=0.1, axis="y", color="#30363d")
        ax_v.set_title("Trading Volume", color="#e6edf3", fontsize=11)
        fig_v.tight_layout(); st.pyplot(fig_v, use_container_width=True); plt.close(fig_v)

        st.subheader("Raw OHLCV Data")
        ohlcv = df_p[["date","open","high","low","close","volume"]].sort_values("date", ascending=False).head(50).copy()
        for c in ["open","high","low","close"]:
            ohlcv[c] = ohlcv[c].apply(lambda v: f"{v:.2f}" if pd.notna(v) else "")
        show_table(ohlcv)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: INDICATORS
# ══════════════════════════════════════════════════════════════════════════════
elif "Indicators" in page:
    st.title(f"📉 Technical Indicators – {NAMES.get(active_ticker)}")

    prices = api_get("prices",     {"ticker": active_ticker, "period": "2Y"}) or []
    inds   = api_get("indicators", {"ticker": active_ticker}) or []

    if inds:
        tab1, tab2, tab3, tab4 = st.tabs(["RSI", "MACD", "Bollinger Bands", "ADX"])

        with tab1:
            fig = fig_rsi(inds, active_ticker)
            st.pyplot(fig, use_container_width=True); plt.close(fig)
            df_i = pd.DataFrame(inds)
            latest_rsi = df_i["rsi_14"].dropna().iloc[-1]
            zone = "🔴 Overbought" if latest_rsi > 70 else ("🟢 Oversold" if latest_rsi < 30 else "🟡 Neutral")
            st.metric("Latest RSI-14", f"{latest_rsi:.2f}", zone)

        with tab2:
            fig = fig_macd(inds, active_ticker)
            st.pyplot(fig, use_container_width=True); plt.close(fig)
            df_i = pd.DataFrame(inds)
            latest_hist = df_i["macd_hist"].dropna().iloc[-1]
            st.metric("MACD Histogram", f"{latest_hist:.4f}",
                      "Bullish" if latest_hist > 0 else "Bearish")

        with tab3:
            if prices:
                fig = fig_bollinger(prices, inds, active_ticker)
                st.pyplot(fig, use_container_width=True); plt.close(fig)
            df_i = pd.DataFrame(inds)
            bp = df_i["bb_pct"].dropna().iloc[-1]
            st.metric("BB %B", f"{bp:.4f}", "Near Upper Band" if bp > 0.8 else ("Near Lower Band" if bp < 0.2 else "Mid Range"))

        with tab4:
            df_i = pd.DataFrame(inds)
            df_i["date"] = pd.to_datetime(df_i["date"])
            fig_adx, ax_adx = plt.subplots(figsize=(11, 3.5), facecolor=DARK)
            ax_adx.set_facecolor(DARK)
            ax_adx.plot(df_i["date"], df_i["adx"], color="#ffa657", lw=2, label="ADX")
            ax_adx.axhline(25, color="#58a6ff", ls="--", lw=1, label="Trend threshold (25)")
            ax_adx.set_title(f"{NAMES.get(active_ticker)} – ADX", color="#e6edf3", fontsize=12, fontweight="bold")
            ax_adx.tick_params(colors="#8b949e"); ax_adx.legend(facecolor=SURF, labelcolor="#e6edf3", fontsize=9)
            for spine in ax_adx.spines.values(): spine.set_edgecolor("#30363d")
            ax_adx.grid(alpha=0.12, color="#30363d"); fig_adx.tight_layout()
            st.pyplot(fig_adx, use_container_width=True); plt.close(fig_adx)

        st.subheader("Latest Indicator Values")
        df_i = pd.DataFrame(inds).tail(10)
        show_ind_cols = ["date", "sma_20", "sma_50", "rsi_14", "macd",
                         "macd_signal", "bb_pct", "atr_14", "mfi_14", "adx"]
        avail = [c for c in show_ind_cols if c in df_i.columns]
        ind_disp = df_i[avail].sort_values("date", ascending=False).copy()
        for c in avail:
            if c != "date":
                ind_disp[c] = ind_disp[c].apply(lambda v: f"{v:.4f}" if pd.notna(v) else "")
        show_table(ind_disp)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: EDA
# ══════════════════════════════════════════════════════════════════════════════
elif "EDA" in page:
    st.title("🔍 Exploratory Data Analysis")

    # Load pre-computed figures
    fig_map = {
        "price_history.png":        "Normalised Price History",
        "daily_returns_dist.png":   "Daily Return Distributions",
        "correlation_heatmap.png":  "Return Correlation Heatmap",
        "volatility_rolling.png":   "30-Day Rolling Volatility",
        "volume_trend.png":         "30-Day Rolling Average Volume",
    }
    for fname, title in fig_map.items():
        fpath = os.path.join(FIGURES_DIR, fname)
        if os.path.exists(fpath):
            st.subheader(title)
            st.image(fpath, use_container_width=True)
            st.divider()

    st.subheader("Candlestick Samples (Last 90 Days)")
    c1, c2 = st.columns(2)
    for i, ticker in enumerate(TICKERS):
        fname = f"candlestick_{ticker.replace('.','_')}.png"
        fpath = os.path.join(FIGURES_DIR, fname)
        if os.path.exists(fpath):
            (c1 if i % 2 == 0 else c2).image(fpath, caption=NAMES[ticker], use_container_width=True)

    st.subheader("Full EDA Summary Statistics")
    eda_path = os.path.join("reports", "eda_summary.csv")
    if os.path.exists(eda_path):
        df = pd.read_csv(eda_path)
        df_disp = df.copy()
        for c in df_disp.select_dtypes("number").columns:
            df_disp[c] = df_disp[c].apply(lambda v: f"{v:.2f}" if pd.notna(v) else "")
        show_table(df_disp)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ML MODELS
# ══════════════════════════════════════════════════════════════════════════════
elif "ML Models" in page:
    st.title("🤖 Machine Learning Models")
    st.caption("Walk-Forward TimeSeriesSplit CV (5 folds) · Binary classification: Close[t+1] > Close[t]")

    metrics = api_get("model_metrics") or []
    if metrics:
        st.subheader("Model Performance – Walk-Forward CV")
        fig = fig_model_metrics(metrics)
        st.pyplot(fig, use_container_width=True); plt.close(fig)

        st.subheader("Detailed CV Metrics Table")
        df_m = pd.DataFrame(metrics)
        fmt_cols = ["accuracy","precision","recall","f1","roc_auc"]
        df_m_disp = df_m.copy()
        for c in fmt_cols:
            if c in df_m_disp.columns:
                df_m_disp[c] = df_m_disp[c].apply(lambda v: f"{v:.4f}" if pd.notna(v) else "")
        show_table(df_m_disp)

    st.divider()
    preds = api_get("predictions", {"ticker": active_ticker}) or []
    if preds:
        st.subheader(f"Prediction Signals on Test Set – {NAMES.get(active_ticker)}")
        fig = fig_prediction_signals(preds, active_ticker)
        st.pyplot(fig, use_container_width=True); plt.close(fig)

        df_preds = pd.DataFrame(preds)
        total_correct = df_preds["correct"].sum()
        total = len(df_preds)
        acc = total_correct / total * 100 if total else 0
        c1, c2, c3 = st.columns(3)
        c1.metric("Test Rows", total)
        c2.metric("Correct Predictions", int(total_correct))
        c3.metric("Test Accuracy", f"{acc:.2f}%")

    st.divider()
    st.subheader("Feature Importance Charts")
    for ticker in TICKERS:
        for mn in ["LightGBM", "RandomForest", "XGBoost"]:
            fname = f"feature_importance_{ticker.replace('.','_')}_{mn}.png"
            fpath = os.path.join(FIGURES_DIR, fname)
            if os.path.exists(fpath):
                st.image(fpath, caption=f"{NAMES[ticker]} – {mn}", use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: BACKTESTING
# ══════════════════════════════════════════════════════════════════════════════
elif "Backtesting" in page:
    st.title("⏳ Backtesting Results")
    st.caption("ML Signal Strategy (prob≥0.55 → Long) vs Buy & Hold · Test set = last 20% of data")

    bt = api_get("backtest") or []
    if bt:
        df_bt = pd.DataFrame(bt)
        st.subheader("Performance Summary")
        fig = fig_backtest(bt)
        st.pyplot(fig, use_container_width=True); plt.close(fig)

        st.subheader("Detailed Backtest Table")
        num_cols = [c for c in df_bt.columns if c != "ticker"]
        for c in num_cols:
            df_bt[c] = pd.to_numeric(df_bt[c], errors="coerce")
        df_bt_disp = df_bt.rename(columns={"ticker":"Ticker"}).copy()
        for c in num_cols:
            df_bt_disp[c] = df_bt_disp[c].apply(lambda v: f"{v:.2f}" if pd.notna(v) else "")
        show_table(df_bt_disp)

        st.subheader("Equity Curves")
        c1, c2 = st.columns(2)
        for i, ticker in enumerate(TICKERS):
            slug = ticker.replace(".", "_")
            fpath = os.path.join(FIGURES_DIR, f"backtest_equity_{slug}.png")
            if os.path.exists(fpath):
                (c1 if i % 2 == 0 else c2).image(fpath, caption=NAMES[ticker], use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: LIVE PREDICT
# ══════════════════════════════════════════════════════════════════════════════
elif "Live Predict" in page:
    st.title("🎯 Live ML Prediction")
    st.caption("Runs the trained model on the latest available feature row")

    col_left, col_right = st.columns([1, 2])
    with col_left:
        st.subheader("Get Signal")
        predict_ticker = st.selectbox(
            "Select Stock", TICKERS,
            format_func=lambda t: f"{NAMES[t]} ({t})"
        )
        if st.button("🔮 Predict Now", type="primary", use_container_width=True):
            with st.spinner("Running model…"):
                result = api_post("predict", {"ticker": predict_ticker})
            if result and "error" not in result:
                st.session_state["last_pred"] = result
            elif result:
                st.error(result.get("error", "Unknown error"))

        if "last_pred" in st.session_state:
            res = st.session_state["last_pred"]
            signal = res.get("signal", "N/A")
            is_buy = signal == "BUY"
            st.divider()
            if is_buy:
                st.success(f"### 🟢 {signal}")
            else:
                st.warning(f"### 🟡 {signal}")
            prob = res.get("prob_up", 0)
            st.metric("Probability UP", f"{prob*100:.1f}%")
            st.metric("Confidence",     f"{res.get('confidence', 0):.1f}%")
            st.metric("Latest Close",   f"₹{res.get('close', 0):,.2f}")
            st.metric("Date",           res.get("date", "N/A"))
            st.progress(float(prob))

    with col_right:
        st.subheader(f"Prediction History – {NAMES.get(active_ticker)}")
        preds = api_get("predictions", {"ticker": active_ticker}) or []
        if preds:
            fig = fig_prediction_signals(preds, active_ticker)
            st.pyplot(fig, use_container_width=True); plt.close(fig)

            df_p = pd.DataFrame(preds)
            st.subheader("Recent Prediction Log")
            pred_disp = df_p[["date","close","predicted_up","prob_up","actual_target","correct"]].sort_values("date", ascending=False).head(20).copy()
            pred_disp["close"]   = pred_disp["close"].apply(lambda v: f"{v:.2f}" if pd.notna(v) else "")
            pred_disp["prob_up"] = pred_disp["prob_up"].apply(lambda v: f"{v:.4f}" if pd.notna(v) else "")
            show_table(pred_disp)
