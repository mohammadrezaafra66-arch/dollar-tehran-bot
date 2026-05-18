@echo off
cd /d %~dp0
call setup_env.bat
if errorlevel 1 exit /b 1
start "Afra Dashboard" cmd /k "call .venv\Scripts\activate && python dashboard.py"
start "Afra Bot Loop" cmd /k "call .venv\Scripts\activate && python main.py run-loop"
