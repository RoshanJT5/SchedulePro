# Redis Server Startup Script (for Windows)
# Run this to start Redis server locally

@echo off
echo Redis Server Startup Helper
echo.

REM Check if Redis is installed
if exist "redis-server.exe" (
    echo ✅ Found redis-server.exe in current directory
    echo Starting Redis server...
    start "Redis Server" redis-server.exe
    timeout /t 2 >nul
    echo.
    echo ✅ Redis server started!
    echo.
) else (
    echo ❌ redis-server.exe not found in current directory
    echo.
    echo Options to install/run Redis on Windows:
    echo.
    echo OPTION 1: Download Redis for Windows
    echo   1. Visit: https://github.com/microsoftarchive/redis/releases
    echo   2. Download Redis-x64-3.0.504.zip
    echo   3. Extract to this folder
    echo   4. Run this script again
    echo.
    echo OPTION 2: Use WSL (Windows Subsystem for Linux)
    echo   1. Install WSL if not already installed
    echo   2. Open WSL terminal
    echo   3. Run: sudo apt-get install redis-server
    echo   4. Run: sudo service redis-server start
    echo.
    echo OPTION 3: Use Docker
    echo   docker run -d -p 6379:6379 redis:alpine
    echo.
    echo OPTION 4: Skip Redis (run synchronously)
    echo   - The app will work without Redis but slower
    echo   - Timetable generation runs synchronously in request thread
    echo.
    pause
    exit /b 1
)

echo Next step: Run start_celery.bat to start the worker
pause
