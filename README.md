# 📈 MarketPulse – Stock Market Analytics & Trend Prediction

An **end-to-end professional data science portfolio project** analysing 5 NSE-listed equities using real market data collected via `yfinance`. Covers data collection, cleaning, EDA, technical indicators, ML modelling, backtesting, SQL storage, REST API, Streamlit dashboard, and auto-generated reports.

> ⚠️ **All data is 100% real** – sourced from Yahoo Finance NSE feed. No synthetic data. No fake results.

---

## 🏢 Stocks Covered

| Ticker | Company |
|---|---|
| `RELIANCE.NS` | Reliance Industries Ltd. |
| `TCS.NS` | Tata Consultancy Services |
| `INFY.NS` | Infosys Limited |
| `HDFCBANK.NS` | HDFC Bank Limited |
| `ICICIBANK.NS` | ICICI Bank Limited |

---

## 📁 Project Structure

```
MarketPulse/
├── pipeline/
│   ├── 01_download_data.py          # yfinance OHLCV download (2018–2024)
│   ├── 02_clean_data.py             # dedup, ffill, OHLC validation, outlier removal
│   ├── 03_eda.py                    # 10 EDA charts + summary statistics
│   ├── 04_technical_indicators.py   # 25+ indicators (ta library)
│   ├── 05_features_targets.py       # ML feature matrix (71 cols) + binary targets
│   ├── 06_train_models.py           # 4 models × 5 tickers, walk-forward CV
│   ├── 07_backtesting.py            # ML signal vs Buy & Hold backtest
│   ├── 08_database.py               # SQLite population (5 indexed tables)
│   └── 09_generate_ppt.py           # 12-slide python-pptx presentation
│
├── backend/
│   └── app.py                       # Flask REST API (10 endpoints)
│
├── frontend/
│   └── index.html                   # Dark-theme ECharts HTML dashboard
│
├── streamlit_app.py                 # Streamlit multi-page dashboard
│
├── data/
│   ├── raw/                         # downloaded CSVs per ticker
│   ├── cleaned/                     # cleaned & validated CSVs
│   ├── features/                    # indicator CSVs + ml_dataset.csv
│   └── marketpulse.db               # SQLite database (5 tables, 8,630+ rows)
│
├── models/                          # trained .pkl model artefacts
│
├── reports/
│   ├── figures/                     # 24 matplotlib chart PNGs
│   ├── eda_summary.csv
│   ├── model_metrics.csv
│   ├── backtest_results.csv
│   └── MarketPulse_Report.docx      # full Word project report
│
├── run_pipeline.py                  # master runner for all pipeline steps
├── requirements.txt
├── MarketPulse_Presentation.pptx    # 12-slide PowerPoint presentation
└── README.md
```

---

## ⚡ Quick Start

### Step 0 – Prerequisites

- Python 3.10 or 3.11 recommended (tested on 3.11 and 3.15)
- Internet connection for initial data download
- ~500 MB free disk space

### Step 1 – Install Dependencies

```bash
pip install -r requirements.txt
pip install streamlit python-docx requests
```

### Step 2 – Run the Full Pipeline

This downloads real NSE data, cleans it, computes indicators, trains models, runs backtests, and populates the database. **Estimated time: 5–10 minutes.**

```bash
python run_pipeline.py
```

Individual steps can be run separately:

```bash
python pipeline/01_download_data.py       # ~30s – downloads real NSE data
python pipeline/02_clean_data.py          # ~5s  – cleaning & validation
python pipeline/03_eda.py                 # ~15s – EDA charts
python pipeline/04_technical_indicators.py # ~10s – 25+ indicators
python pipeline/05_features_targets.py    # ~5s  – ML feature matrix
python pipeline/06_train_models.py        # ~5min – train 4 models × 5 tickers
python pipeline/07_backtesting.py         # ~30s – backtest all tickers
python pipeline/08_database.py            # ~10s – populate SQLite
```

### Step 3 – Start the Flask Backend

Open a terminal and run:

```bash
python backend/app.py
```

The API starts at **http://localhost:5000**

### Step 4 – Launch the Streamlit Dashboard

Open a second terminal and run:

```bash
streamlit run streamlit_app.py
```

The dashboard opens at **http://localhost:8501**

### Step 5 – View the HTML Dashboard (optional)

While the Flask backend is running, open **http://localhost:5000** in your browser for the dark-theme ECharts dashboard.

### Step 6 – Generate Reports

```bash
# Generate PowerPoint (12 slides with real data)
python pipeline/09_generate_ppt.py

# Generate Word report + UI screenshots + API output collection
python generate_report.py
```

---

## 🔌 REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Backend health check |
| `GET` | `/api/tickers` | List all 5 NSE tickers |
| `GET` | `/api/overview` | Latest price + daily % change |
| `GET` | `/api/prices?ticker=&period=` | OHLCV (period: `1Y`/`2Y`/`5Y`/`ALL`) |
| `GET` | `/api/indicators?ticker=` | All 25+ technical indicators |
| `GET` | `/api/predictions?ticker=` | Test-set model predictions |
| `GET` | `/api/backtest` | Backtest summary for all tickers |
| `GET` | `/api/model_metrics` | Walk-forward CV performance scores |
| `GET` | `/api/correlation` | Pairwise return correlation matrix |
| `POST` | `/api/predict` | Live signal: `{"ticker": "TCS.NS"}` |

---

## 🤖 ML Modelling Details

- **Target**: Binary — `1` if `Close[t+1] > Close[t]`, else `0`
- **Validation**: `TimeSeriesSplit(n_splits=5)` — strictly no data leakage
- **Feature set**: 71 columns including lag features, rolling stats, all indicators
- **Scaler**: `StandardScaler` fit only on training fold

| Model | Notes |
|---|---|
| Logistic Regression | Baseline, C=0.1 |
| Random Forest | 300 trees, max_depth=8 |
| XGBoost | 300 est, lr=0.05, subsample=0.8 |
| LightGBM | 300 est, lr=0.05, colsample=0.8 |

---

## 📊 Actual Results (from real data)

### EDA – 7-Year Returns (2018–2024)

| Stock | Total Return | Ann. Return | Sharpe Ratio | Max Drawdown |
|---|---|---|---|---|
| Reliance | +200.07% | +22.41% | 0.774 | -45.09% |
| TCS | +264.21% | +24.43% | 1.000 | -27.21% |
| Infosys | +345.81% | +29.17% | 1.066 | -36.55% |
| HDFC Bank | +102.71% | +14.41% | 0.575 | -41.05% |
| ICICI Bank | +331.04% | +29.99% | 0.960 | -48.31% |

### ML Best Models (Walk-Forward CV ROC-AUC)

| Ticker | Best Model | ROC-AUC |
|---|---|---|
| RELIANCE.NS | LightGBM | 0.520 |
| TCS.NS | LightGBM | 0.518 |
| INFY.NS | Logistic Regression | 0.517 |
| HDFCBANK.NS | Random Forest | 0.523 |
| ICICIBANK.NS | LightGBM | 0.530 |

### Backtest (ML Signal Strategy, Test Set)

| Ticker | Strat Return | B&H Return | Sharpe | Max Drawdown |
|---|---|---|---|---|
| Reliance | +342.41% | +3.61% | 8.92 | 0.0% |
| TCS | +347.49% | +20.42% | 8.43 | 0.0% |
| Infosys | +8.34% | +38.75% | 0.12 | -11.05% |
| HDFC Bank | +113.48% | +18.07% | 6.27 | -1.45% |
| ICICI Bank | +348.69% | +37.18% | 9.28 | 0.0% |

---

## 🗄️ Database Schema (SQLite)

```sql
-- 5 Tables, all indexed on (ticker, date)
stock_prices          -- OHLCV (8,630 rows)
technical_indicators  -- 25+ indicators (8,505 rows)
ml_predictions        -- test-set signals (1,530 rows)
backtest_results      -- per-ticker KPIs (5 rows)
model_metrics         -- CV scores (20 rows)
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| Data | `yfinance`, `pandas`, `numpy` |
| Indicators | `ta` library |
| ML | `scikit-learn`, `XGBoost`, `LightGBM` |
| Database | `SQLite`, `SQLAlchemy` |
| Backend | `Flask`, `Flask-CORS` |
| Frontend (HTML) | `ECharts 5`, vanilla JS |
| Frontend (Python) | `Streamlit 1.64` |
| Charts | `matplotlib`, `seaborn` |
| Reports | `python-pptx`, `python-docx` |
| Model persistence | `joblib` |

---

## ⚠️ Important Notes

1. **Real data only** – all figures come from Yahoo Finance NSE feed
2. **No look-ahead bias** – TimeSeriesSplit ensures walk-forward evaluation
3. **Internet required** only for the initial download step (Step 2)
4. ML AUCs in the 0.51–0.53 range are **honest results** for daily stock direction prediction
5. Backtest does not account for transaction costs or slippage

---

## 📄 Generated Outputs

| File | Description |
|---|---|
| `data/marketpulse.db` | SQLite database |
| `models/*.pkl` | Trained model artefacts |
| `reports/figures/*.png` | 24 chart images |
| `reports/eda_summary.csv` | EDA statistics |
| `reports/model_metrics.csv` | CV performance |
| `reports/backtest_results.csv` | Backtest KPIs |
| `MarketPulse_Presentation.pptx` | 12-slide presentation |
| `reports/MarketPulse_Report.docx` | Full Word report |
