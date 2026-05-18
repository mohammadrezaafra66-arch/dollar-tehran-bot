@echo off
cd /d %~dp0
start "Afra Dashboard" start_dashboard.bat
start "Afra Bot Loop" run_loop.bat
