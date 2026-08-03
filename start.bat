@echo off
setlocal

echo ========================================
echo G3 Bot Panel - Windows Setup
echo ========================================
echo.

REM ============================================
REM Step 1: Check Python
REM ============================================
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10 or later.
    pause
    exit /b 1
)
echo OK - Python found.
echo.

REM ============================================
REM Step 2: Create virtual environment
REM ============================================
echo [2/6] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)
echo.

REM ============================================
REM Step 3: Activate virtual environment and install requirements
REM ============================================
echo [3/6] Installing Python dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r panel-backend\requirements.txt
echo Dependencies installed.
echo.

REM ============================================
REM Step 4: Check Node.js for frontend
REM ============================================
echo [4/6] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Node.js is not installed.
    echo Frontend will not work without Node.js.
    echo Please install Node.js 18 or later from https://nodejs.org/
) else (
    echo OK - Node.js found.
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)
echo.

REM ============================================
REM Step 5: Setup environment variables
REM ============================================
echo [5/6] Checking environment variables...
if not exist ".env" (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo Please edit .env file with your configuration.
) else (
    echo .env file exists.
)
echo.

REM ============================================
REM Step 6: Start the backend and frontend
REM ============================================
echo [6/6] Starting services...
echo.

echo Starting Panel Backend...
start "G3 Panel Backend" /MIN cmd /c "call venv\Scripts\activate.bat && cd panel-backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8100"

timeout /t 3 /nobreak >nul

echo Starting Frontend...
start "G3 Frontend" /MIN cmd /c "cd frontend && npm run dev"

timeout /t 5 /nobreak >nul

echo ========================================
echo Services started!
echo Panel API: http://localhost:8100
echo Frontend:  http://localhost:3010
echo ========================================
echo.

start http://localhost:3010

echo Done!
pause
