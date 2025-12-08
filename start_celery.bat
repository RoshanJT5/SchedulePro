# Celery Worker Startup Script
# Run this to start the Celery worker for background task processing

@echo off
echo Starting Celery worker for timetable generation...
echo.

REM Check if Redis is running
echo Checking Redis connection...
python -c "import redis; r = redis.Redis(host='localhost', port=6379); r.ping(); print('✅ Redis is running')" 2>nul
if errorlevel 1 (
    echo ❌ Redis is not running!
    echo.
    echo Please start Redis first:
    echo 1. Download Redis for Windows from: https://github.com/microsoftarchive/redis/releases
    echo 2. Extract and run redis-server.exe
    echo 3. Or install via WSL: wsl sudo service redis-server start
    echo.
    pause
    exit /b 1
)

echo.
echo Starting Celery worker...
echo Press Ctrl+C to stop
echo.

REM Start Celery worker
celery -A app_with_navigation.celery worker --pool=solo --loglevel=info

pause
