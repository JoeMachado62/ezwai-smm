#!/bin/bash
# EZWAI SMM V3.0 - Production Startup with Gunicorn
# Runs the application as a production WSGI server with auto-restart

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Configuration
APP_MODULE="app_v3:app"
WORKERS=4  # Number of worker processes
BIND_ADDRESS="0.0.0.0:5000"
LOG_FILE="logs/gunicorn.log"
ACCESS_LOG="logs/access.log"
ERROR_LOG="logs/error.log"
PID_FILE="gunicorn.pid"

# Create logs directory
mkdir -p logs

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "ERROR: Virtual environment not found. Run start_v3.sh first."
    exit 1
fi

# Check if Gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "Installing Gunicorn..."
    pip install gunicorn
fi

# Stop existing instance if running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "Stopping existing instance (PID: $OLD_PID)..."
        kill $OLD_PID
        sleep 2
    fi
    rm -f "$PID_FILE"
fi

echo "========================================"
echo "EZWAI SMM V3.0 - Production Mode"
echo "========================================"
echo ""
echo "Starting with Gunicorn..."
echo "Workers: $WORKERS"
echo "Bind address: $BIND_ADDRESS"
echo "Logs: $LOG_FILE"
echo ""

# Start Gunicorn with auto-restart on file changes
gunicorn "$APP_MODULE" \
    --workers $WORKERS \
    --bind $BIND_ADDRESS \
    --pid $PID_FILE \
    --daemon \
    --log-file "$LOG_FILE" \
    --access-logfile "$ACCESS_LOG" \
    --error-logfile "$ERROR_LOG" \
    --log-level info \
    --timeout 300 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50

if [ $? -eq 0 ]; then
    echo "Application started successfully!"
    echo "PID: $(cat $PID_FILE)"
    echo ""
    echo "Application is now running at:"
    echo "  http://localhost:5000"
    echo ""
    echo "To view logs:"
    echo "  tail -f $LOG_FILE"
    echo ""
    echo "To stop:"
    echo "  ./stop_v3.sh"
else
    echo "ERROR: Failed to start application"
    exit 1
fi