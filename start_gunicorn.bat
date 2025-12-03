@echo off
REM Quick start script for AI Timetable Generator with Gunicorn (Windows)

echo ========================================
echo AI Timetable Generator - Gunicorn Start
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM Check if .env file exists
if not exist ".env" (
    echo Warning: .env file not found!
    if exist ".env.example" (
        echo Creating .env from .env.example...
        copy .env.example .env
        echo Created .env file. Please edit it with your configuration.
        echo.
        pause
    ) else (
        echo Error: .env.example not found. Please create .env manually.
        pause
        exit /b 1
    )
)

REM Start Gunicorn
echo.
echo ========================================
echo Starting Gunicorn server...
echo Server will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo ========================================
echo.

gunicorn -c gunicorn_config.py app_with_navigation:app

pause
