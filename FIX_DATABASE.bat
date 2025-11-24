@echo off
echo ================================================
echo  FIXING INSTRUCTORS TABLE - PlanSphere Database
echo ================================================
echo.
echo This will add the missing columns to your instructors table.
echo.
echo Database: plansphere
echo User: plansphere
echo Host: localhost:5432
echo.
pause

REM Set password environment variable
set PGPASSWORD=plansphere

REM Try to find psql in common locations
set PSQL_PATH=

if exist "C:\Program Files\PostgreSQL\15\bin\psql.exe" set PSQL_PATH=C:\Program Files\PostgreSQL\15\bin\psql.exe
if exist "C:\Program Files\PostgreSQL\14\bin\psql.exe" set PSQL_PATH=C:\Program Files\PostgreSQL\14\bin\psql.exe
if exist "C:\Program Files\PostgreSQL\13\bin\psql.exe" set PSQL_PATH=C:\Program Files\PostgreSQL\13\bin\psql.exe
if exist "C:\Program Files\PostgreSQL\16\bin\psql.exe" set PSQL_PATH=C:\Program Files\PostgreSQL\16\bin\psql.exe
if exist "C:\Program Files (x86)\PostgreSQL\15\bin\psql.exe" set PSQL_PATH=C:\Program Files (x86)\PostgreSQL\15\bin\psql.exe

if "%PSQL_PATH%"=="" (
    echo ERROR: Could not find psql.exe
    echo.
    echo Please manually run the SQL commands from URGENT_FIX_INSTRUCTORS.sql
    echo using pgAdmin or another PostgreSQL client.
    echo.
    pause
    exit /b 1
)

echo Found PostgreSQL at: %PSQL_PATH%
echo.
echo Running SQL commands...
echo.

"%PSQL_PATH%" -U plansphere -h localhost -d plansphere -f "URGENT_FIX_INSTRUCTORS.sql"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================
    echo  SUCCESS! Database updated successfully!
    echo ================================================
    echo.
    echo Next steps:
    echo 1. Restart your FastAPI server (Ctrl+C and run again)
    echo 2. Refresh your browser (Ctrl+F5)
    echo 3. Try adding an instructor again
    echo.
) else (
    echo.
    echo ================================================
    echo  ERROR: Failed to update database
    echo ================================================
    echo.
    echo Please run the SQL manually using pgAdmin:
    echo 1. Open pgAdmin
    echo 2. Connect to database: plansphere
    echo 3. Open Query Tool
    echo 4. Open file: URGENT_FIX_INSTRUCTORS.sql
    echo 5. Execute (F5)
    echo.
)

pause
