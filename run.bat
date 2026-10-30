@echo off
title 5G-EdgeAgri — System Launcher
color 0A

echo =====================================================================
echo       5G-EDGE AGRI: REAL-TIME SMART AGRICULTURE FRAMEWORK
echo       Team 14 - 1NT24CS202 (Prajwal Karadi) ^& 1NT24CS190 (Padavala Rishi)
echo =====================================================================
echo.

:: Check for Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python 3 was not found in PATH. Please install Python.
    pause
    exit /b 1
)

:: Check for Node.js
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js was not found in PATH. Please install Node.js.
    pause
    exit /b 1
)

:: Check Virtual Environment
if not exist "venv\Scripts\activate.bat" (
    echo [*] Creating Python virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [*] Installing backend dependencies...
    pip install -r backend\requirements.txt
) else (
    call venv\Scripts\activate.bat
)

:: Seed database if needed
echo [*] Initializing SQLite database and verifying seed data...
python scripts\seed_demo_data.py

:: Check Frontend node_modules
if not exist "frontend\node_modules" (
    echo [*] Installing frontend npm dependencies...
    cd frontend
    call npm install
    cd ..
)

echo.
echo =====================================================================
echo  [+] Starting 5G-EdgeAgri Backend Server (FastAPI + SQLite + MQTT)...
echo  [+] FastAPI API & WebSockets: http://127.0.0.1:8000
echo  [+] Interactive Swagger API Docs: http://127.0.0.1:8000/docs
echo =====================================================================
start "5G-EdgeAgri Backend (FastAPI)" cmd /k "venv\Scripts\python -m uvicorn backend.app.main:app --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo.
echo =====================================================================
echo  [+] Starting 5G-EdgeAgri Farmer Dashboard (React + Vite)...
echo  [+] Dashboard UI: http://localhost:3000
echo =====================================================================
start "5G-EdgeAgri Dashboard (React)" cmd /k "cd frontend && npm run dev"

timeout /t 4 /nobreak >nul

:: Launch Browser
echo [*] Opening 5G-EdgeAgri Farmer Dashboard in browser...
start http://localhost:3000

echo.
echo =====================================================================
echo  [SUCCESS] 5G-EdgeAgri Framework is running!
echo  Press any key in this window to exit launcher (services remain running).
echo =====================================================================
pause
