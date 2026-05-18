@echo off
cd /d %~dp0

if not exist .venv (
  echo Creating Python virtual environment...
  py -m venv .venv
  if errorlevel 1 (
    echo ERROR: Could not create .venv
    pause
    exit /b 1
  )
)

call .venv\Scripts\activate

if not exist .venv\.deps_installed (
  echo Installing Python packages. Please wait...
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  if errorlevel 1 (
    echo ERROR: Package installation failed.
    echo Close all bot/dashboard windows, run repair_venv.bat, then try again.
    pause
    exit /b 1
  )
  echo ok > .venv\.deps_installed
) else (
  echo Python packages already installed.
)

exit /b 0
