"""
MarketPulse – indicators.py
Entry-point alias for pipeline Step 4: compute technical indicators.
Runs 04_technical_indicators.py directly so both filenames are equivalent.
"""
import os, runpy

runpy.run_path(
    os.path.join(os.path.dirname(__file__), "04_technical_indicators.py"),
    run_name="__main__",
)
