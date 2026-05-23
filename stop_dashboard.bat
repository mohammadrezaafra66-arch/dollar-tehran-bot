@echo off
echo Stopping Afra dashboard on port 8090...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8090 ^| findstr LISTENING') do (
    echo Killing process %%a
    taskkill /PID %%a /F
)
echo Done.
pause
