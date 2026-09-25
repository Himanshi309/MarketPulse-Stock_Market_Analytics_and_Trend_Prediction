@echo off
REM ============================================================
REM  MarketPulse – Full Pipeline Runner (run ONCE, first time)
REM  This downloads data, trains models, builds the database.
REM  Takes 5-10 minutes. Internet required for data download.
REM ============================================================

cd /d "%~dp0"

echo.
echo  ==========================================
echo   MarketPulse – Running Full Pipeline
echo   (Downloads real NSE data + trains models)
echo  ==========================================
echo.

python run_pipeline.py

echo.
echo  Pipeline complete! Now run START_PROJECT.bat
echo.
pause
