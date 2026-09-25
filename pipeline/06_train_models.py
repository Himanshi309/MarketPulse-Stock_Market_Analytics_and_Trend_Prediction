"""
Step 7 – Train ML models.

Models trained per ticker (classification, Target_1d):
  1. Logistic Regression     (baseline)
  2. Random Forest Classifier
  3. XGBoost Classifier
  4. LightGBM Classifier

Walk-forward time-series split (TimeSeriesSplit, n_splits=5).
Metrics: Accuracy, Precision, Recall, F1, ROC-AUC.
Best model per ticker saved as joblib in models/.
Feature importances saved to reports/feature_importance_<ticker>.csv.
All metrics saved to reports/model_metrics.csv.
"""

import os
import warnings
import joblib
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection    import TimeSeriesSplit
from sklearn.preprocessing      import StandardScaler
from sklearn.linear_model       import LogisticRegression
from sklearn.ensemble           import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics            import (accuracy_score, precision_score,
                                        recall_score, f1_score, roc_auc_score,
                                        classification_report, confusion_matrix,
                                        ConfusionMatrixDisplay)
from xgboost   import XGBClassifier
from lightgbm  import LGBMClassifier

warnings.filterwarnings("ignore")

FEATURES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "features")
MODELS_DIR   = os.path.join(os.path.dirname(__file__), "..", "models")
REPORTS_DIR  = os.path.join(os.path.dirname(__file__), "..", "reports")
FIGURES_DIR  = os.path.join(REPORTS_DIR, "figures")
TICKERS      = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
TARGET       = "Target_1d"
N_SPLITS     = 5

EXCLUDE_COLS = ["Target_1d", "Target_5d", "Target_Return_1d", "Ticker",
                "Open", "High", "Low", "Close", "Volume"]   # avoid look-ahead via raw price


def get_feature_cols(df: pd.DataFrame) -> list:
    return [c for c in df.columns if c not in EXCLUDE_COLS]


def evaluate(y_true, y_pred, y_prob) -> dict:
    return {
        "Accuracy":  round(accuracy_score(y_true, y_pred),  4),
        "Precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "Recall":    round(recall_score(y_true, y_pred, zero_division=0),    4),
        "F1":        round(f1_score(y_true, y_pred, zero_division=0),        4),
        "ROC_AUC":   round(roc_auc_score(y_true, y_prob),   4),
    }


def plot_confusion_matrix(cm, title, out_path):
    fig, ax = plt.subplots(figsize=(4, 3))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Down", "Up"])
    disp.plot(ax=ax, colorbar=False, cmap="Blues")
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close()


def plot_feature_importance(importances: pd.Series, ticker: str, model_name: str):
    top = importances.nlargest(20)
    fig, ax = plt.subplots(figsize=(8, 6))
    top.sort_values().plot.barh(ax=ax, color="#3B82F6")
    ax.set_title(f"Top-20 Feature Importances\n{ticker} – {model_name}",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("Importance")
    fig.tight_layout()
    fname = f"feature_importance_{ticker.replace('.', '_')}_{model_name}.png"
    plt.savefig(os.path.join(FIGURES_DIR, fname), dpi=130, bbox_inches="tight")
    plt.close()


def train_ticker(ticker: str, df_ticker: pd.DataFrame, all_metrics: list):
    print(f"\n{'='*60}")
    print(f"  {ticker}")
    print(f"{'='*60}")

    feature_cols = get_feature_cols(df_ticker)
    X = df_ticker[feature_cols].values
    y = df_ticker[TARGET].values

    # ── Walk-forward CV ───────────────────────────────────────────────────────
    tscv   = TimeSeriesSplit(n_splits=N_SPLITS)
    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000, C=0.1, random_state=42),
        "RandomForest":       RandomForestClassifier(n_estimators=300, max_depth=8,
                                                     min_samples_leaf=20, random_state=42,
                                                     n_jobs=-1),
        "XGBoost":            XGBClassifier(n_estimators=300, max_depth=5,
                                            learning_rate=0.05, subsample=0.8,
                                            colsample_bytree=0.8,
                                            use_label_encoder=False,
                                            eval_metric="logloss",
                                            random_state=42, verbosity=0),
        "LightGBM":           LGBMClassifier(n_estimators=300, max_depth=5,
                                             learning_rate=0.05, subsample=0.8,
                                             colsample_bytree=0.8,
                                             random_state=42, verbose=-1),
    }

    best_auc   = -1
    best_name  = None
    best_model = None

    for model_name, model in models.items():
        fold_metrics = []
        for train_idx, test_idx in tscv.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            scaler  = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_test  = scaler.transform(X_test)

            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_prob = model.predict_proba(X_test)[:, 1]
            fold_metrics.append(evaluate(y_test, y_pred, y_prob))

        avg = pd.DataFrame(fold_metrics).mean().to_dict()
        avg.update({"Ticker": ticker, "Model": model_name})
        all_metrics.append(avg)

        print(f"  {model_name:<22} "
              f"Acc={avg['Accuracy']:.3f}  "
              f"F1={avg['F1']:.3f}  "
              f"AUC={avg['ROC_AUC']:.3f}")

        if avg["ROC_AUC"] > best_auc:
            best_auc  = avg["ROC_AUC"]
            best_name = model_name

    # ── Retrain best model on full data ──────────────────────────────────────
    print(f"\n  Best model: {best_name}  (AUC={best_auc:.3f})")
    scaler     = StandardScaler()
    X_scaled   = scaler.fit_transform(X)
    final_model = models[best_name]
    final_model.fit(X_scaled, y)

    # Save artefacts
    ticker_slug = ticker.replace(".", "_")
    joblib.dump({"model": final_model, "scaler": scaler, "features": feature_cols},
                os.path.join(MODELS_DIR, f"{ticker_slug}_model.pkl"))

    # Feature importances (for tree-based models)
    if hasattr(final_model, "feature_importances_"):
        imp = pd.Series(final_model.feature_importances_, index=feature_cols)
        imp_df = imp.sort_values(ascending=False).reset_index()
        imp_df.columns = ["Feature", "Importance"]
        imp_df.to_csv(os.path.join(REPORTS_DIR,
                                   f"feature_importance_{ticker_slug}.csv"), index=False)
        plot_feature_importance(imp, ticker, best_name)

    # Confusion matrix on last CV fold
    tscv2 = TimeSeriesSplit(n_splits=N_SPLITS)
    *_, (train_idx, test_idx) = tscv2.split(X)
    X_tr = scaler.fit_transform(X[train_idx])
    X_te = scaler.transform(X[test_idx])
    final_model.fit(X_tr, y[train_idx])
    y_pred_last = final_model.predict(X_te)
    cm = confusion_matrix(y[test_idx], y_pred_last)
    plot_confusion_matrix(cm, f"{ticker} – {best_name}",
                          os.path.join(FIGURES_DIR,
                                       f"cm_{ticker_slug}.png"))


def main():
    os.makedirs(MODELS_DIR,  exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    ml_df = pd.read_csv(os.path.join(FEATURES_DIR, "ml_dataset.csv"),
                        parse_dates=["Date"], index_col="Date")

    all_metrics = []
    for ticker in TICKERS:
        df_t = ml_df[ml_df["Ticker"] == ticker].sort_index()
        if len(df_t) < 300:
            print(f"  Skipping {ticker}: insufficient data ({len(df_t)} rows)")
            continue
        train_ticker(ticker, df_t, all_metrics)

    metrics_df = pd.DataFrame(all_metrics)[
        ["Ticker", "Model", "Accuracy", "Precision", "Recall", "F1", "ROC_AUC"]]
    metrics_path = os.path.join(REPORTS_DIR, "model_metrics.csv")
    metrics_df.to_csv(metrics_path, index=False)
    print(f"\n\nAll model metrics saved → {metrics_path}")
    print(metrics_df.to_string(index=False))


if __name__ == "__main__":
    main()
