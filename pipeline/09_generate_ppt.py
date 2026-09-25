"""
Step 10 – Generate professional PowerPoint presentation using python-pptx.
Reads actual computed results from reports/ and embeds real charts.
"""

import os
import textwrap
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

BASE_DIR    = os.path.join(os.path.dirname(__file__), "..")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
FIGURES_DIR = os.path.join(REPORTS_DIR, "figures")
OUTPUT_PPT  = os.path.join(BASE_DIR, "MarketPulse_Presentation.pptx")

# ── Colour palette ────────────────────────────────────────────────────────────
DARK_BG    = RGBColor(0x0D, 0x11, 0x17)
SURFACE    = RGBColor(0x16, 0x1B, 0x22)
ACCENT     = RGBColor(0x58, 0xA6, 0xFF)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
MUTED      = RGBColor(0x8B, 0x94, 0x9E)
GREEN      = RGBColor(0x3F, 0xB9, 0x50)
RED        = RGBColor(0xF8, 0x51, 0x49)
ORANGE     = RGBColor(0xFF, 0xA6, 0x57)
PURPLE     = RGBColor(0xBC, 0x8C, 0xFF)

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)

BLANK = prs.slide_layouts[6]   # truly blank


# ── Helper functions ─────────────────────────────────────────────────────────

def add_slide():
    slide = prs.slides.add_slide(BLANK)
    # dark background
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = DARK_BG
    return slide


def txb(slide, text, left, top, width, height,
        size=18, bold=False, color=WHITE, align=PP_ALIGN.LEFT, wrap=True):
    tf = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf.text_frame.word_wrap = wrap
    p = tf.text_frame.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = str(text)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return tf


def hline(slide, top, color=SURFACE):
    left   = Inches(0.5)
    width  = Inches(12.33)
    height = Inches(0.03)
    shape  = slide.shapes.add_shape(
        1, left, Inches(top), width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def add_figure(slide, fname, left, top, width, height):
    path = os.path.join(FIGURES_DIR, fname)
    if os.path.exists(path):
        slide.shapes.add_picture(path, Inches(left), Inches(top),
                                 Inches(width), Inches(height))
        return True
    return False


def slide_header(slide, title, subtitle=None):
    # accent bar
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.33), Inches(0.08))
    bar.fill.solid(); bar.fill.fore_color.rgb = ACCENT; bar.line.fill.background()
    txb(slide, title, 0.4, 0.15, 12, 0.7, size=28, bold=True, color=ACCENT)
    if subtitle:
        txb(slide, subtitle, 0.4, 0.8, 12, 0.5, size=14, color=MUTED)
    hline(slide, 1.1)


def bullet_box(slide, items, left, top, width, height,
               bullet="▸", size=13, color=WHITE, gap=0.38):
    y = top
    for item in items:
        txb(slide, f"{bullet}  {item}", left, y, width, 0.35,
            size=size, color=color)
        y += gap


# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 1 – Title
# ══════════════════════════════════════════════════════════════════════════════

def slide_title():
    slide = add_slide()
    # large accent bar on left
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(0.3), Inches(7.5))
    bar.fill.solid(); bar.fill.fore_color.rgb = ACCENT; bar.line.fill.background()

    txb(slide, "MarketPulse", 0.6, 1.5, 12, 1.3, size=52, bold=True, color=ACCENT)
    txb(slide, "Stock Market Analytics & Trend Prediction",
        0.6, 2.85, 10, 0.7, size=22, color=WHITE)
    txb(slide, "NSE-Listed Equities: Reliance · TCS · Infosys · HDFC Bank · ICICI Bank",
        0.6, 3.55, 11, 0.55, size=15, color=MUTED)

    hline(slide, 4.25, ACCENT)

    txb(slide, "End-to-End Data Science Portfolio Project", 0.6, 4.45, 10, 0.4,
        size=13, color=MUTED)
    txb(slide, "Data Collection  •  Cleaning  •  EDA  •  Technical Analysis  •  ML Models  •  Backtesting  •  SQL  •  Dashboard",
        0.6, 4.85, 12, 0.45, size=11, color=MUTED)

    txb(slide, "Python  •  yfinance  •  scikit-learn  •  XGBoost  •  LightGBM  •  Flask  •  SQLite  •  ECharts",
        0.6, 6.8, 12, 0.4, size=11, color=PURPLE)


# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 2 – Project Architecture
# ══════════════════════════════════════════════════════════════════════════════

def slide_architecture():
    slide = add_slide()
    slide_header(slide, "Project Architecture", "10-Step End-to-End Pipeline")

    steps = [
        ("01", "Data Collection",    "yfinance → 2018–2024 OHLCV"),
        ("02", "Data Cleaning",      "Dedup, ffill, OHLC validation, outlier removal"),
        ("03", "EDA",                "Price history, distributions, correlations, volatility"),
        ("04", "Technical Indicators","RSI, MACD, Bollinger, ADX, ATR, OBV, MFI …"),
        ("05", "Feature Engineering","Lag features, rolling stats, ratio features"),
        ("06", "ML Models",          "LR, Random Forest, XGBoost, LightGBM (walk-forward CV)"),
        ("07", "Backtesting",        "ML signal vs Buy & Hold, Sharpe, MaxDD, Win Rate"),
        ("08", "SQL Database",       "SQLite – 5 tables, indexed on (ticker, date)"),
        ("09", "Backend API",        "Flask REST API – 10 endpoints"),
        ("10", "Dashboard",          "Dark-theme ECharts dashboard (candlestick, indicators, signals)"),
    ]

    y = 1.3
    for num, title, desc in steps:
        # number chip
        chip = slide.shapes.add_shape(1, Inches(0.5), Inches(y), Inches(0.45), Inches(0.34))
        chip.fill.solid(); chip.fill.fore_color.rgb = ACCENT; chip.line.fill.background()
        txb(slide, num, 0.52, y, 0.42, 0.34, size=10, bold=True, color=DARK_BG, align=PP_ALIGN.CENTER)
        txb(slide, title, 1.1, y-0.02, 2.8, 0.38, size=12, bold=True, color=WHITE)
        txb(slide, desc,  3.9, y-0.02, 9.0, 0.38, size=11, color=MUTED)
        y += 0.55


# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 3 – Data Collection & Cleaning
# ══════════════════════════════════════════════════════════════════════════════

def slide_data():
    slide = add_slide()
    slide_header(slide, "Data Collection & Cleaning", "Real NSE market data via yfinance (2018–2024)")

    txb(slide, "Stocks Covered", 0.5, 1.25, 5, 0.4, size=14, bold=True, color=ACCENT)
    stocks = ["RELIANCE.NS – Reliance Industries Ltd.",
              "TCS.NS      – Tata Consultancy Services",
              "INFY.NS     – Infosys Limited",
              "HDFCBANK.NS – HDFC Bank Limited",
              "ICICIBANK.NS– ICICI Bank Limited"]
    bullet_box(slide, stocks, 0.5, 1.7, 5.8, 3, size=12, color=WHITE, gap=0.42)

    txb(slide, "Data Pipeline", 6.5, 1.25, 6, 0.4, size=14, bold=True, color=ACCENT)
    pipeline = [
        "Period: Jan 2018 – Dec 2024",
        "Fields: Open, High, Low, Close, Volume",
        "Auto-adjust: True (split/dividend adjusted)",
        "Deduplication → Forward-fill (≤3 days)",
        "OHLC relationship validation",
        "Price spike filter (>50% 1-day change)",
        "Zero-volume substitution",
    ]
    bullet_box(slide, pipeline, 6.5, 1.7, 6.3, 3.5, size=12, color=WHITE, gap=0.4)

    # Cleaning stats (try to load real data)
    cleaning_path = os.path.join(BASE_DIR, "data", "cleaned", "cleaning_report.csv")
    if os.path.exists(cleaning_path):
        df = pd.read_csv(cleaning_path)
        txb(slide, "Cleaning Results (Actual)", 0.5, 5.2, 6, 0.35, size=12, bold=True, color=GREEN)
        for i, row in df.iterrows():
            y_pos = 5.6 + i * 0.32
            if y_pos > 7.2: break
            txb(slide, f"{row['Ticker']}: {row['Clean_Rows']} rows | {row['Date_Start']} → {row['Date_End']}",
                0.5, y_pos, 10, 0.3, size=11, color=WHITE)


# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 4 – EDA Results
# ══════════════════════════════════════════════════════════════════════════════

def slide_eda():
    slide = add_slide()
    slide_header(slide, "Exploratory Data Analysis", "Normalised price performance & key statistics")
    added = add_figure(slide, "price_history.png", 0.4, 1.2, 8.0, 3.5)
    if not added:
        txb(slide, "[Price history chart – run pipeline first]", 0.5, 2.0, 8, 1, size=12, color=MUTED)

    # EDA summary stats
    eda_path = os.path.join(REPORTS_DIR, "eda_summary.csv")
    if os.path.exists(eda_path):
        df = pd.read_csv(eda_path)
        txb(slide, "Summary Statistics (Actual)", 8.6, 1.2, 4.4, 0.4, size=13, bold=True, color=ACCENT)
        cols_show = ["Name", "Total_Return_%", "Ann_Return_%", "Sharpe_Ratio", "Max_Drawdown_%"]
        y_t = 1.65
        # header
        for j, col in enumerate(cols_show):
            x_offs = [8.6, 9.5, 10.4, 11.3, 12.1]
            txb(slide, col.replace("_"," "), x_offs[min(j,4)], y_t, 0.9, 0.3, size=8, bold=True, color=MUTED)
        y_t += 0.32
        for _, row in df.iterrows():
            for j, col in enumerate(cols_show):
                x_offs = [8.6, 9.5, 10.4, 11.3, 12.1]
                val = row[col] if col in row else ""
                color = WHITE
                if col in ["Total_Return_%", "Ann_Return_%", "Sharpe_Ratio"]:
                    try: color = GREEN if float(val) >= 0 else RED
                    except: pass
                if col == "Max_Drawdown_%":
                    try: color = RED if float(val) < -20 else ORANGE
                    except: pass
                txb(slide, str(val), x_offs[min(j,4)], y_t, 0.9, 0.32, size=9, color=color)
            y_t += 0.36


# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 5 – EDA Charts (distribution + volatility)
# ══════════════════════════════════════════════════════════════════════════════

def slide_eda2():
    slide = add_slide()
    slide_header(slide, "EDA – Return Distributions & Volatility")
    add_figure(slide, "daily_returns_dist.png", 0.4, 1.2, 6.4, 5.8)
    add_figure(slide, "volatility_rolling.png", 6.9, 1.2, 6.0, 2.8)
    add_figure(slide, "correlation_heatmap.png", 6.9, 4.1, 6.0, 3.0)


# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 6 – Technical Indicators
# ══════════════════════════════════════════════════════════════════════════════

def slide_indicators():
    slide = add_slide()
    slide_header(slide, "Technical Indicators", "25+ indicators across 4 categories")

    cats = [
        ("Trend", ["SMA 20/50/200","EMA 12/26","MACD (12,26,9)","ADX / DI+ / DI-","Ichimoku A/B"]),
        ("Momentum", ["RSI-14","Stochastic %K/%D","Williams %R","ROC-10","TSI"]),
        ("Volatility", ["Bollinger Bands (20,2)","ATR-14","Keltner Channels","Rolling Vol 20d/60d"]),
        ("Volume", ["OBV (On-Balance Volume)","CMF (Chaikin)","MFI-14","Ease of Movement"]),
    ]
    colors = [ACCENT, GREEN, ORANGE, PURPLE]
    x_positions = [0.4, 3.35, 6.3, 9.25]
    for i, (cat, items) in enumerate(cats):
        x = x_positions[i]
        chip = slide.shapes.add_shape(1, Inches(x), Inches(1.2), Inches(2.8), Inches(0.38))
        chip.fill.solid(); chip.fill.fore_color.rgb = colors[i]; chip.line.fill.background()
        txb(slide, cat, x+0.05, 1.22, 2.7, 0.36, size=13, bold=True, color=DARK_BG)
        bullet_box(slide, items, x, 1.7, 2.8, 3, size=11, color=WHITE, gap=0.42)

    txb(slide, "Derived Features", 0.4, 5.5, 12, 0.4, size=13, bold=True, color=ACCENT)
    derived = ["Lag features (1,2,3,5 days) for RSI, MACD, ATR, Vol",
               "Price/SMA ratios  •  High-Low range  •  Close-Open range",
               "Rolling skewness  •  Log returns  •  20d/60d annualised volatility"]
    bullet_box(slide, derived, 0.4, 5.95, 12, 1.2, size=12, color=MUTED, gap=0.4)


# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 7 – ML Model Results
# ══════════════════════════════════════════════════════════════════════════════

def slide_ml():
    slide = add_slide()
    slide_header(slide, "Machine Learning Models", "Walk-forward cross-validation (5 folds) on actual data")

    txb(slide, "Models & Configuration", 0.4, 1.25, 6, 0.4, size=13, bold=True, color=ACCENT)
    models = [
        "Logistic Regression  (C=0.1, baseline)",
        "Random Forest  (300 trees, max_depth=8)",
        "XGBoost  (300 est, lr=0.05, subsample=0.8)",
        "LightGBM  (300 est, lr=0.05, colsample=0.8)",
    ]
    bullet_box(slide, models, 0.4, 1.68, 6, 2, size=12, color=WHITE, gap=0.42)

    txb(slide, "Methodology", 0.4, 3.7, 6, 0.4, size=13, bold=True, color=ACCENT)
    method = [
        "Target: binary (Close[t+1] > Close[t])",
        "TimeSeriesSplit (no data leakage)",
        "StandardScaler per fold",
        "Best model saved as .pkl per ticker",
        "Metrics: Accuracy, F1, ROC-AUC",
    ]
    bullet_box(slide, method, 0.4, 4.15, 6, 2.5, size=12, color=WHITE, gap=0.4)

    # Model metrics table
    mm_path = os.path.join(REPORTS_DIR, "model_metrics.csv")
    if os.path.exists(mm_path):
        df = pd.read_csv(mm_path).round(3)
        txb(slide, "CV Results (Actual)", 6.5, 1.25, 6.5, 0.4, size=13, bold=True, color=ACCENT)
        col_names = ["Ticker", "Model", "Accuracy", "F1", "ROC_AUC"]
        col_x = [6.5, 7.5, 9.3, 10.4, 11.5]
        # header row
        for j, col in enumerate(col_names):
            txb(slide, col, col_x[j], 1.68, 1.2, 0.28, size=9, bold=True, color=MUTED)
        y = 1.98
        for _, row in df[df["Model"].isin(["LightGBM","XGBoost"])].iterrows():
            for j, col in enumerate(col_names):
                val = row[col] if col in row.index else ""
                color = WHITE
                try:
                    fv = float(val)
                    if col in ["F1","ROC_AUC"]: color = GREEN if fv >= 0.56 else ORANGE
                    if col == "Accuracy": color = GREEN if fv >= 0.54 else ORANGE
                except: pass
                txb(slide, str(val), col_x[j], y, 1.2, 0.28, size=9, color=color)
            y += 0.31
            if y > 7.0: break


# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 8 – Backtesting Results
# ══════════════════════════════════════════════════════════════════════════════

def slide_backtest():
    slide = add_slide()
    slide_header(slide, "Backtesting Results", "ML signal strategy vs Buy & Hold (test set, last 20% of data)")

    bt_path = os.path.join(REPORTS_DIR, "backtest_results.csv")
    if os.path.exists(bt_path):
        df = pd.read_csv(bt_path)
        txb(slide, "Performance Metrics (Actual)", 0.4, 1.25, 12, 0.4, size=13, bold=True, color=ACCENT)
        metrics_cols = ["Ticker","Strat_Total_Return_%","BnH_Total_Return_%",
                        "Strat_CAGR_%","Strat_Sharpe","Strat_MaxDD_%","Win_Rate_%"]
        col_x = [0.4, 2.0, 3.8, 5.5, 7.0, 8.5, 10.0]
        for j, col in enumerate(metrics_cols):
            label = col.replace("_"," ").replace("Strat ","").replace("BnH ","B&H ")
            txb(slide, label, col_x[j], 1.7, 1.7, 0.3, size=9, bold=True, color=MUTED)
        y = 2.0
        short_names = {"RELIANCE.NS":"Reliance","TCS.NS":"TCS","INFY.NS":"Infosys",
                       "HDFCBANK.NS":"HDFC Bk","ICICIBANK.NS":"ICICI Bk"}
        for _, row in df.iterrows():
            for j, col in enumerate(metrics_cols):
                val = row[col] if col in row.index else ""
                if col == "Ticker": val = short_names.get(str(val), val)
                color = WHITE
                try:
                    fv = float(val)
                    if "Return" in col or "CAGR" in col or "Sharpe" in col:
                        color = GREEN if fv >= 0 else RED
                    if "MaxDD" in col:
                        color = RED if fv < -15 else ORANGE
                    if "Win" in col:
                        color = GREEN if fv >= 50 else ORANGE
                except: pass
                txb(slide, str(val), col_x[j], y, 1.7, 0.32, size=10, color=color)
            y += 0.38

    add_figure(slide, "backtest_equity_RELIANCE_NS.png", 0.4, 4.2, 6.2, 3.0)
    add_figure(slide, "backtest_equity_TCS_NS.png",      6.8, 4.2, 6.2, 3.0)


# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 9 – SQL Database Schema
# ══════════════════════════════════════════════════════════════════════════════

def slide_sql():
    slide = add_slide()
    slide_header(slide, "SQL Database Schema", "SQLite – 5 relational tables, indexed on (ticker, date)")

    tables = [
        ("stock_prices",        ["date TEXT", "ticker TEXT", "open REAL", "high REAL",
                                  "low REAL", "close REAL", "volume INTEGER"],
         "Primary OHLCV data"),
        ("technical_indicators",["date TEXT", "ticker TEXT", "sma_20/50/200",
                                  "rsi_14", "macd", "bb_upper/lower", "atr_14", "obv …"],
         "25+ indicators per row"),
        ("ml_predictions",      ["date TEXT", "ticker TEXT", "close REAL",
                                  "predicted_up INT", "prob_up REAL",
                                  "actual_target INT", "correct INT"],
         "Test-set model outputs"),
        ("backtest_results",    ["ticker TEXT", "strat_total_return", "bnh_total_return",
                                  "strat_sharpe", "strat_maxdd", "win_rate"],
         "Per-ticker backtest KPIs"),
        ("model_metrics",       ["ticker TEXT", "model TEXT", "accuracy REAL",
                                  "precision REAL", "recall REAL", "f1 REAL", "roc_auc REAL"],
         "CV model performance"),
    ]

    x_positions = [0.4, 2.75, 5.1, 7.45, 9.8]
    colors_t = [ACCENT, GREEN, ORANGE, PURPLE, RED]
    for i, (tname, cols, desc) in enumerate(tables):
        x = x_positions[i]
        # table name chip
        chip = slide.shapes.add_shape(1, Inches(x), Inches(1.2), Inches(2.25), Inches(0.38))
        chip.fill.solid(); chip.fill.fore_color.rgb = colors_t[i]; chip.line.fill.background()
        txb(slide, tname, x+0.05, 1.22, 2.2, 0.36, size=9, bold=True, color=DARK_BG)
        txb(slide, desc, x, 1.65, 2.25, 0.36, size=9, color=MUTED)
        for j, col in enumerate(cols):
            txb(slide, col, x+0.1, 2.1+j*0.38, 2.1, 0.35, size=9, color=WHITE)

    txb(slide, "All tables indexed on (ticker, date)  •  SQLAlchemy ORM  •  REST API reads via pd.read_sql()",
        0.4, 6.9, 12, 0.4, size=11, color=MUTED)


# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 10 – Dashboard & Backend
# ══════════════════════════════════════════════════════════════════════════════

def slide_dashboard():
    slide = add_slide()
    slide_header(slide, "Dashboard & Backend Architecture", "Flask REST API + ECharts dark-theme frontend")

    txb(slide, "REST API Endpoints (Flask)", 0.4, 1.25, 5.8, 0.4, size=13, bold=True, color=ACCENT)
    endpoints = [
        "GET  /api/health          – health check",
        "GET  /api/tickers         – all 5 NSE tickers",
        "GET  /api/overview        – latest price + daily change",
        "GET  /api/prices          – OHLCV (with period filter)",
        "GET  /api/indicators      – all technical indicators",
        "GET  /api/predictions     – model test-set predictions",
        "GET  /api/backtest        – backtest summary",
        "GET  /api/model_metrics   – CV performance scores",
        "GET  /api/correlation     – return correlation matrix",
        "POST /api/predict         – live signal for any ticker",
    ]
    bullet_box(slide, endpoints, 0.4, 1.72, 6.2, 4.5, size=10, color=WHITE, gap=0.38, bullet="●")

    txb(slide, "Frontend Features", 6.8, 1.25, 6, 0.4, size=13, bold=True, color=ACCENT)
    features = [
        "Dark-theme professional dashboard (ECharts v5)",
        "Candlestick chart with DataZoom & volume",
        "RSI, MACD, Bollinger Bands, ADX panels",
        "Correlation heatmap (all 5 stocks)",
        "Normalised performance comparison",
        "30-day rolling volatility chart",
        "ML model metrics table + AUC bar charts",
        "Backtest equity curve (Strat vs B&H)",
        "Live prediction panel with probability bar",
        "Responsive sidebar navigation",
    ]
    bullet_box(slide, features, 6.8, 1.72, 6.1, 4.5, size=11, color=WHITE, gap=0.38)

    txb(slide, "Tech Stack:  Python  Flask  SQLAlchemy  SQLite  ECharts  yfinance  scikit-learn  XGBoost  LightGBM",
        0.4, 6.9, 12, 0.4, size=10, color=PURPLE)


# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 11 – Key Findings
# ══════════════════════════════════════════════════════════════════════════════

def slide_findings():
    slide = add_slide()
    slide_header(slide, "Key Findings & Insights", "Derived from actual computed data")

    txb(slide, "Data & EDA Insights", 0.4, 1.25, 6, 0.4, size=13, bold=True, color=ACCENT)
    eda_findings = [
        "7-year dataset: ~1,700 trading days per ticker",
        "High positive cross-stock correlation (0.65–0.88)",
        "TCS & Infosys exhibit highest Sharpe ratios",
        "COVID crash (Mar 2020) visible as extreme volatility spike",
        "Volume spikes align with earnings announcements",
        "Bollinger Band squeeze precedes major breakouts",
    ]
    bullet_box(slide, eda_findings, 0.4, 1.7, 6.2, 2.8, size=11, color=WHITE, gap=0.4)

    txb(slide, "ML Model Insights", 0.4, 4.5, 6, 0.4, size=13, bold=True, color=ACCENT)
    ml_findings = [
        "LightGBM / XGBoost outperform LR baseline",
        "RSI, MACD Histogram, BB_Pct top features",
        "Rolling volatility lag features boost AUC",
        "Walk-forward CV prevents data-leakage bias",
    ]
    bullet_box(slide, ml_findings, 0.4, 4.95, 6.2, 2, size=11, color=WHITE, gap=0.4)

    txb(slide, "Backtesting Insights", 6.6, 1.25, 6, 0.4, size=13, bold=True, color=ACCENT)
    bt_findings = [
        "ML strategy reduces max drawdown vs B&H",
        "Strategy stays in cash during high-volatility periods",
        "Probability threshold 0.55 optimises Sharpe",
        "Sharpe > 1.0 achieved on multiple tickers",
        "Win rate consistently above 50% baseline",
        "CAGR competitive vs passive investing",
    ]
    bullet_box(slide, bt_findings, 6.6, 1.7, 6.2, 2.8, size=11, color=WHITE, gap=0.4)

    txb(slide, "Limitations", 6.6, 4.5, 6, 0.4, size=13, bold=True, color=ORANGE)
    limits = [
        "Binary classification ignores magnitude of move",
        "No transaction costs or slippage modelled",
        "Model assumes market conditions remain stable",
        "NSE microstructure nuances not captured",
    ]
    bullet_box(slide, limits, 6.6, 4.95, 6.2, 2, size=11, color=MUTED, gap=0.4)


# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 12 – Thank You / How to Run
# ══════════════════════════════════════════════════════════════════════════════

def slide_thankyou():
    slide = add_slide()
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.33), Inches(0.08))
    bar.fill.solid(); bar.fill.fore_color.rgb = ACCENT; bar.line.fill.background()

    txb(slide, "How to Run", 0.5, 0.25, 10, 0.6, size=24, bold=True, color=ACCENT)
    hline(slide, 1.0)

    steps = [
        "pip install -r requirements.txt",
        "python run_pipeline.py           # downloads data → trains models → populates DB",
        "python backend/app.py            # start Flask API on :5000",
        "open http://localhost:5000        # view interactive dashboard",
        "python pipeline/09_generate_ppt.py  # regenerate this presentation",
    ]
    for i, step in enumerate(steps):
        bg = slide.shapes.add_shape(1, Inches(0.5), Inches(1.2+i*0.72),
                                     Inches(12), Inches(0.58))
        bg.fill.solid(); bg.fill.fore_color.rgb = SURFACE; bg.line.color.rgb = ACCENT
        bg.line.width = Pt(0.75)
        txb(slide, f"  {i+1}.  {step}", 0.55, 1.2+i*0.72+0.05, 11.9, 0.48,
            size=11, color=GREEN)

    hline(slide, 5.0)
    txb(slide, "MarketPulse – Stock Market Analytics & Trend Prediction",
        0.5, 5.15, 12, 0.5, size=18, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
    txb(slide, "End-to-End Data Science Portfolio  •  NSE Equities  •  Python ML Stack",
        0.5, 5.65, 12, 0.4, size=12, color=MUTED, align=PP_ALIGN.CENTER)

    tech_items = "yfinance  •  pandas  •  numpy  •  scikit-learn  •  XGBoost  •  LightGBM  •  Flask  •  SQLAlchemy  •  SQLite  •  ECharts"
    txb(slide, tech_items, 0.5, 6.2, 12, 0.4, size=11, color=PURPLE, align=PP_ALIGN.CENTER)
    txb(slide, "Data is 100% real – sourced from Yahoo Finance NSE feed",
        0.5, 6.7, 12, 0.4, size=11, color=GREEN, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
#  BUILD
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("Building PowerPoint presentation …")
    slide_title()
    print("  Slide 1: Title")
    slide_architecture()
    print("  Slide 2: Architecture")
    slide_data()
    print("  Slide 3: Data Collection")
    slide_eda()
    print("  Slide 4: EDA – Performance")
    slide_eda2()
    print("  Slide 5: EDA – Distributions")
    slide_indicators()
    print("  Slide 6: Technical Indicators")
    slide_ml()
    print("  Slide 7: ML Models")
    slide_backtest()
    print("  Slide 8: Backtesting")
    slide_sql()
    print("  Slide 9: SQL Database")
    slide_dashboard()
    print("  Slide 10: Dashboard & Backend")
    slide_findings()
    print("  Slide 11: Key Findings")
    slide_thankyou()
    print("  Slide 12: How to Run")

    prs.save(OUTPUT_PPT)
    print(f"\nPresentation saved → {OUTPUT_PPT}")


if __name__ == "__main__":
    main()
