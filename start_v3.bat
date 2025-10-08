@echo off
REM EZWAI SMM V3.0 - Windows Startup Script
REM Checks dependencies, starts MySQL (if needed), and runs the application

echo ========================================
echo EZWAI SMM V3.0 - Startup Script
echo ========================================
echo.

REM Set working directory
cd /d "%~dp0"
echo Current directory: %CD%
echo.

REM Check Python installation
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)
python --version
echo.

REM Check required packages
echo [2/6] Checking dependencies...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo WARNING: Flask not found. Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo Dependencies OK
)
echo.

REM Check .env file
echo [3/6] Checking environment configuration...
if not exist ".env" (
    echo ERROR: .env file not found
    echo Please create .env file with required configuration
    pause
    exit /b 1
)
echo .env file found
echo.

REM Check MySQL service (Windows) - Optional for XAMPP/WAMP users
echo [4/6] Checking MySQL service...
sc query MySQL >nul 2>&1
if errorlevel 1 (
    echo WARNING: MySQL service not found
    echo Checking for MySQL80 service...
    sc query MySQL80 >nul 2>&1
    if errorlevel 1 (
        echo NOTE: No MySQL Windows service found
        echo This is normal if using XAMPP/WAMP
        echo Database connection will be tested in next step...
        goto :skip_mysql_service
    ) else (
        set MYSQL_SERVICE=MySQL80
    )
) else (
    set MYSQL_SERVICE=MySQL
)

REM Check if MySQL is running (only if service was found)
sc query %MYSQL_SERVICE% | find "RUNNING" >nul
if errorlevel 1 (
    echo MySQL service found but not running. Starting...
    net start %MYSQL_SERVICE%
    if errorlevel 1 (
        echo WARNING: Failed to start MySQL service
        echo Please start MySQL manually or run this script as Administrator
        echo Database connection will be tested in next step...
        goto :skip_mysql_service
    )
    echo MySQL started successfully
) else (
    echo MySQL service is running
)

:skip_mysql_service
echo.

REM Check database connection
echo [5/6] Testing database connection...
python -c "from app_v3 import app, db; app.app_context().push(); db.engine.connect(); print('Database connection: OK')" 2>nul
if errorlevel 1 (
    echo ERROR: Cannot connect to database
    echo Please check your database credentials in .env file
    echo - DB_USERNAME
    echo - DB_PASSWORD
    echo - DB_HOST
    echo - DB_NAME
    pause
    exit /b 1
)
echo.

REM Check for existing app process
echo [6/6] Checking for running instances...
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *app_v3.py*" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo WARNING: Application may already be running
    echo Press Ctrl+C to cancel, or
    pause
)
echo.

REM Start the application
echo ========================================
echo Starting EZWAI SMM V3.0...
echo ========================================
echo.
echo Application will be available at:
echo   http://localhost:5000
echo   http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the application
echo.
python app_v3.py

REM If we get here, the app exited
echo.
echo ========================================
echo Application stopped
echo ========================================
pause