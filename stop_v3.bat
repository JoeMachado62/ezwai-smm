@echo off
REM EZWAI SMM V3.0 - Stop Script

echo ========================================
echo EZWAI SMM V3.0 - Stop Script
echo ========================================
echo.

echo Searching for running Python processes...
tasklist /FI "IMAGENAME eq python.exe" | find /I "python.exe"

echo.
echo Stopping all Flask/Python processes on port 5000...

REM Kill processes by port 5000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000.*LISTENING"') do (
    echo Killing PID: %%a
    taskkill /F /PID %%a 2>nul
)

REM Also kill any Python process running app_v3.py
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /NH') do (
    wmic process where "ProcessId=%%a AND CommandLine like '%%app_v3.py%%'" delete 2>nul
)

REM Also kill any Flask processes
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /NH') do (
    wmic process where "ProcessId=%%a AND CommandLine like '%%flask%%'" delete 2>nul
)

echo.
echo All Flask processes stopped
echo ========================================
pause