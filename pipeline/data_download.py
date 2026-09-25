"""
MarketPulse – data_download.py
Entry-point alias for pipeline Step 1: download historical OHLCV data.
Runs 01_download_data.py directly so both filenames are equivalent.
"""
import os, runpy

runpy.run_path(
    os.path.join(os.path.dirname(__file__), "01_download_data.py"),
    run_name="__main__",
)
