@echo off
REM EZWAI SMM V3.0 - Stop Script

echo ========================================
echo EZWAI SMM V3.0 - Stop Script
echo ========================================
echo.

echo Searching for running Python processes...
tasklist /FI "IMAGENAME eq python.exe" | find /I "python.exe"

echo.
echo Stopping all Python processes running app_v3.py...
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /NH') do (
    wmic process where "ProcessId=%%a AND CommandLine like '%%app_v3.py%%'" delete 2>nul
)

echo.
echo Application stopped
echo ========================================
pause