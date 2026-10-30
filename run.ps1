# 5G-EdgeAgri PowerShell Launcher
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host "      5G-EDGE AGRI: REAL-TIME SMART AGRICULTURE FRAMEWORK" -ForegroundColor Green
Write-Host "      Team 14 - 1NT24CS202 (Prajwal Karadi) & 1NT24CS190 (Padavala Rishi)" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host ""

# Ensure venv exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[*] Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    & .\venv\Scripts\pip install -r backend\requirements.txt
}

# Seed database
Write-Host "[*] Seeding database..." -ForegroundColor Yellow
& .\venv\Scripts\python scripts\seed_demo_data.py

# Ensure frontend dependencies
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "[*] Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location frontend
    npm install
    Pop-Location
}

# Launch backend
Write-Host "[+] Launching FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\venv\Scripts\python -m uvicorn backend.app.main:app --port 8000 --reload"

Start-Sleep -Seconds 3

# Launch frontend
Write-Host "[+] Launching React Farmer Dashboard on http://localhost:3000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Start-Sleep -Seconds 4

# Open browser
Start-Process "http://localhost:3000"

Write-Host "[SUCCESS] 5G-EdgeAgri System is running!" -ForegroundColor Green
