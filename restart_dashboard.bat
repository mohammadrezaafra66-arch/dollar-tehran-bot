@echo off
cd /d %~dp0
call stop_dashboard.bat
call start_dashboard.bat
