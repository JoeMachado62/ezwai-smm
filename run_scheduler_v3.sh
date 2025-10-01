#!/bin/bash
# EZWAI SMM V3.0 - Scheduler Runner
# Designed to be run by cron every 5 minutes

# Log file
LOG_FILE="/var/log/ezwai_scheduler_v3.log"

# Timestamp for the log
echo "========================================" >> "$LOG_FILE"
echo "[V3] Script started at $(date)" >> "$LOG_FILE"
echo "Current user: $(whoami)" >> "$LOG_FILE"
echo "Current directory: $(pwd)" >> "$LOG_FILE"

# Set the working directory to script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || {
    echo "Error: Failed to change directory to $SCRIPT_DIR" >> "$LOG_FILE"
    exit 1
}
echo "Changed directory to: $(pwd)" >> "$LOG_FILE"

# Activate the virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "Activated virtual environment" >> "$LOG_FILE"
    echo "Python version: $(python --version 2>&1)" >> "$LOG_FILE"
    echo "Python path: $(which python)" >> "$LOG_FILE"
else
    echo "Error: Virtual environment not found" >> "$LOG_FILE"
    exit 1
fi

# Check if scheduler_v3.py exists
if [ ! -f "scheduler_v3.py" ]; then
    echo "Error: scheduler_v3.py not found in $(pwd)" >> "$LOG_FILE"
    exit 1
fi

# Run the V3 scheduler script
echo "[V3] Running scheduler_v3.py with GPT-5-mini + SeeDream-4" >> "$LOG_FILE"
python scheduler_v3.py >> "$LOG_FILE" 2>&1
SCHEDULER_EXIT_CODE=$?

if [ $SCHEDULER_EXIT_CODE -ne 0 ]; then
    echo "Error: scheduler_v3.py exited with code $SCHEDULER_EXIT_CODE" >> "$LOG_FILE"
else
    echo "[V3] scheduler_v3.py completed successfully" >> "$LOG_FILE"
fi

# Deactivate the virtual environment
deactivate
echo "Deactivated virtual environment" >> "$LOG_FILE"

echo "Script finished at $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo >> "$LOG_FILE"  # Add a blank line for readability between runs

exit $SCHEDULER_EXIT_CODE