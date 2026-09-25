"""
MarketPulse – Master Pipeline Runner
Executes all steps in order:
  1. Download data       (pipeline/data_download.py  → 01_download_data.py)
  2. Clean data          (pipeline/preprocessing.py  → 02_clean_data.py)
  3. EDA                 (pipeline/03_eda.py)
  4. Technical Indicators(pipeline/indicators.py     → 04_technical_indicators.py)
  5. Features & Targets  (pipeline/05_features_targets.py)
  6. Train Models        (pipeline/train.py          → 06_train_models.py)
  7. Backtesting         (pipeline/backtest.py       → 07_backtesting.py)
  8. Database            (pipeline/08_database.py  → database/marketpulse.db)
"""

import subprocess
import sys
import os
import time

STEPS = [
    ("01_download_data.py",      "Step 1 – Download NSE stock data"),
    ("02_clean_data.py",         "Step 2 – Clean data"),
    ("03_eda.py",                "Step 3 – Exploratory Data Analysis"),
    ("04_technical_indicators.py","Step 4 – Technical Indicators"),
    ("05_features_targets.py",   "Step 5 – Build Features & Targets"),
    ("06_train_models.py",       "Step 6 – Train ML Models"),
    ("07_backtesting.py",        "Step 7 – Backtesting"),
    ("08_database.py",           "Step 8 – Populate SQL Database"),
]

PIPELINE_DIR = os.path.join(os.path.dirname(__file__), "pipeline")


def run_step(script: str, label: str) -> bool:
    path = os.path.join(PIPELINE_DIR, script)
    print(f"\n{'─'*60}")
    print(f"  {label}")
    print(f"{'─'*60}")
    t0 = time.time()
    result = subprocess.run(
        [sys.executable, path],
        capture_output=False,
    )
    elapsed = time.time() - t0
    if result.returncode != 0:
        print(f"\n  ❌ FAILED (exit code {result.returncode}) in {elapsed:.1f}s")
        return False
    print(f"\n  ✅ Done in {elapsed:.1f}s")
    return True


def main():
    print("=" * 60)
    print("   MarketPulse – Full Analytics Pipeline")
    print("=" * 60)
    t_start = time.time()
    failed = []
    for script, label in STEPS:
        ok = run_step(script, label)
        if not ok:
            failed.append(label)

    print(f"\n{'='*60}")
    print(f"  Pipeline complete in {time.time()-t_start:.1f}s")
    if failed:
        print(f"  ⚠  Failed steps ({len(failed)}):")
        for f in failed:
            print(f"     • {f}")
    else:
        print("  ✅ All steps completed successfully!")
    print(f"{'='*60}")
    print("\nNext steps:")
    print("  1. Start backend:  python backend/app.py")
    print("  2. Open browser:   http://localhost:5000")
    print("  3. Generate PPT:   python pipeline/09_generate_ppt.py")


if __name__ == "__main__":
    main()
