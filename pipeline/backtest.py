"""
MarketPulse – backtest.py
Entry-point alias for pipeline Step 7: run backtesting.
Runs 07_backtesting.py directly so both filenames are equivalent.
"""
import os, runpy

runpy.run_path(
    os.path.join(os.path.dirname(__file__), "07_backtesting.py"),
    run_name="__main__",
)
