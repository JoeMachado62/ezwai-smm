@echo off
REM EZWAI SMM V3.0 - Windows Background Startup Script
REM Starts the application in the background with auto-restart on crash

echo ========================================
echo EZWAI SMM V3.0 - Background Startup
echo ========================================
echo.

cd /d "%~dp0"

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Generate timestamp for log file
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set LOG_FILE=logs\app_v3_%datetime:~0,8%_%datetime:~8,6%.log

echo Starting application in background...
echo Log file: %LOG_FILE%
echo.

REM Start with auto-restart loop
:restart_loop
echo [%date% %time%] Starting EZWAI SMM V3.0... >> "%LOG_FILE%"
start /B python app_v3.py >> "%LOG_FILE%" 2>&1

REM Wait for process to exit
:check_running
timeout /t 5 /nobreak >nul
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *app_v3.py*" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" goto check_running

REM Process exited, log and restart
echo [%date% %time%] Application crashed or stopped. Restarting in 10 seconds... >> "%LOG_FILE%"
echo Application crashed. Restarting in 10 seconds...
timeout /t 10 /nobreak
goto restart_loop