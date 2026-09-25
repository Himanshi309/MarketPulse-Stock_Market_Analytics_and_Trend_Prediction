@echo off
REM ============================================================
REM  MarketPulse – One-Click Launcher
REM  Double-click this file from Explorer to start the project.
REM  Keep both terminal windows open while using the dashboard.
REM ============================================================

cd /d "%~dp0"

echo.
echo  ==========================================
echo   MarketPulse – Starting Services
echo  ==========================================
echo.

REM -- Check Python --
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found. Install Python 3.10+ and retry.
    pause
    exit /b 1
)

REM -- Start Flask backend in a new window --
echo  [1/2] Starting Flask API backend on http://localhost:5000 ...
start "MarketPulse - Flask Backend" cmd /k "python backend\app.py"

REM -- Wait 3 seconds for Flask to start --
timeout /t 3 /nobreak >nul

REM -- Start Streamlit in a new window --
echo  [2/2] Starting Streamlit dashboard on http://localhost:8501 ...
start "MarketPulse - Streamlit Dashboard" cmd /k "streamlit run streamlit_app.py"

echo.
echo  ==========================================
echo   Both services are starting!
echo.
echo   Flask API  ->  http://localhost:5000
echo   Streamlit  ->  http://localhost:8501
echo.
echo   Your browser should open automatically.
echo   If not, copy the URLs above into Chrome.
echo  ==========================================
echo.
pause
