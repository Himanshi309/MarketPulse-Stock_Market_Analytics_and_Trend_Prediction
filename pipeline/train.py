"""
MarketPulse – train.py
Entry-point alias for pipeline Step 6: train ML models.
Runs 06_train_models.py directly so both filenames are equivalent.
"""
import os, runpy

runpy.run_path(
    os.path.join(os.path.dirname(__file__), "06_train_models.py"),
    run_name="__main__",
)
