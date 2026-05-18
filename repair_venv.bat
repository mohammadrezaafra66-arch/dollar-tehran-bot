@echo off
cd /d %~dp0
echo This will remove the broken Python virtual environment and recreate it.
echo Please close all dashboard/bot CMD windows before continuing.
pause
if exist .venv (
  rmdir /s /q .venv
)
call setup_env.bat
pause
