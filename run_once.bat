@echo off
cd /d %~dp0
call setup_env.bat
if errorlevel 1 exit /b 1
call .venv\Scripts\activate
python main.py run-once
pause
