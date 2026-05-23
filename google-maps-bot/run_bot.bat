@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run.py
) else (
    python run.py
)

if not exist logs mkdir logs
echo %date% %time% - Bot executed >> logs\execution_log.txt
pause
