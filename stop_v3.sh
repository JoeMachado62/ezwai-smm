#!/bin/bash
# EZWAI SMM V3.0 - Stop Script

echo "========================================"
echo "EZWAI SMM V3.0 - Stop Script"
echo "========================================"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Stop Gunicorn if PID file exists
if [ -f "gunicorn.pid" ]; then
    PID=$(cat gunicorn.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping Gunicorn (PID: $PID)..."
        kill $PID
        sleep 2

        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            echo "Force stopping..."
            kill -9 $PID
        fi

        rm -f gunicorn.pid
        echo "Gunicorn stopped"
    else
        echo "Gunicorn PID file exists but process not running"
        rm -f gunicorn.pid
    fi
fi

# Stop any remaining Python processes running app_v3.py
PIDS=$(pgrep -f "python.*app_v3.py")
if [ ! -z "$PIDS" ]; then
    echo "Stopping Python app_v3.py processes..."
    for PID in $PIDS; do
        echo "  Stopping PID: $PID"
        kill $PID 2>/dev/null
    done
    sleep 2

    # Force kill if still running
    PIDS=$(pgrep -f "python.*app_v3.py")
    if [ ! -z "$PIDS" ]; then
        echo "Force stopping remaining processes..."
        for PID in $PIDS; do
            kill -9 $PID 2>/dev/null
        done
    fi
fi

echo ""
echo "Application stopped"
echo "========================================"