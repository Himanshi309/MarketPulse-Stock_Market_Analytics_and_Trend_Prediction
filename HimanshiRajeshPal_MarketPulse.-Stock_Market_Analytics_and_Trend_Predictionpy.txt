"""
Author: Himanshi Rajesh Pal
Project: MarketPulse – Stock Market Analytics & Trend Prediction
Description: End-to-end stock market analytics platform using real NSE data,
technical indicators, machine learning models, Flask REST API, Streamlit dashboard,
SQLite database, and automated reports.
"""
import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run(script):
    print(f"\nRunning {script}...")
    subprocess.run([sys.executable, os.path.join(BASE_DIR, script)], check=True)

def run_pipeline():
    pipeline = [
        "pipeline/01_download_data.py",
        "pipeline/02_clean_data.py",
        "pipeline/03_eda.py",
        "pipeline/04_technical_indicators.py",
        "pipeline/05_features_targets.py",
        "pipeline/06_train_models.py",
        "pipeline/07_backtesting.py",
        "pipeline/08_database.py",
    ]

    for step in pipeline:
        run(step)

    print("\nPipeline completed successfully!")

def generate_outputs():
    run("pipeline/09_generate_ppt.py")
    run("generate_report.py")

if __name__ == "__main__":
    print("=" * 60)
    print(" MarketPulse – Stock Market Analytics & Trend Prediction")
    print(" Author: Shivanand Pal")
    print("=" * 60)

    run_pipeline()
    generate_outputs()

    print("\nProject execution completed successfully.")