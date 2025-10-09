@echo off
echo ========================================
echo Downloading Stripe CLI...
echo ========================================
echo.

powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/stripe/stripe-cli/releases/latest/download/stripe_1.22.0_windows_x86_64.zip' -OutFile 'stripe_cli.zip'}"

echo.
echo ========================================
echo Download complete! File: stripe_cli.zip
echo ========================================
echo.
echo Next step: Extract the ZIP file
echo.
pause
