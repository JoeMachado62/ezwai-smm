@echo off
REM Test Replicate API using curl commands
REM This demonstrates the exact HTTP API calls

setlocal EnableDelayedExpansion

REM Load API token from .env file
for /f "tokens=1,2 delims==" %%a in ('type .env ^| findstr REPLICATE_API_TOKEN') do set REPLICATE_API_TOKEN=%%b

echo ================================================================================
echo REPLICATE API CURL TEST
echo ================================================================================
echo Token: %REPLICATE_API_TOKEN:~0,10%...
echo.

REM Step 1: Create Prediction
echo Step 1: Creating prediction...
echo.

curl -s -X POST ^
  -H "Authorization: Bearer %REPLICATE_API_TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"version\": \"054cd8c667f535616fd66710ce20c8949bf64ac3d9a3459e338f026424be8bec\", \"input\": {\"prompt\": \"Professional business meeting photograph, shot with high-end camera, natural light, bokeh, magazine quality, photorealistic\", \"size\": \"2K\", \"aspect_ratio\": \"16:9\", \"max_images\": 1}}" ^
  https://api.replicate.com/v1/predictions > prediction.json

type prediction.json
echo.
echo.

REM Extract prediction ID from response (requires jq or manual copy)
echo Step 2: Check prediction.json file and copy the "id" field
echo Then run: curl -H "Authorization: Bearer %REPLICATE_API_TOKEN%" https://api.replicate.com/v1/predictions/{PREDICTION_ID}
echo.

pause
