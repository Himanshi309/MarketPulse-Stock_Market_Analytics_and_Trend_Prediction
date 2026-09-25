"""
MarketPulse – preprocessing.py
Entry-point alias for pipeline Step 2: clean raw OHLCV data.
Runs 02_clean_data.py directly so both filenames are equivalent.
"""
import os, runpy

runpy.run_path(
    os.path.join(os.path.dirname(__file__), "02_clean_data.py"),
    run_name="__main__",
)
