#!/bin/bash
# EZWAI SMM V3.0 - Linux/Production Startup Script
# Checks dependencies, services, and starts the application

echo "========================================"
echo "EZWAI SMM V3.0 - Startup Script"
echo "========================================"
echo ""

# Set working directory to script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Current directory: $(pwd)"
echo ""

# Check Python installation
echo "[1/7] Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi
python3 --version
echo ""

# Check pip
echo "[2/7] Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 is not installed"
    exit 1
fi
pip3 --version
echo ""

# Check/create virtual environment
echo "[3/7] Checking virtual environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi
echo "Virtual environment activated"
echo ""

# Check/install dependencies
echo "[4/7] Checking dependencies..."
if ! python -c "import flask" 2>/dev/null; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
else
    echo "Dependencies OK"
fi
echo ""

# Check .env file
echo "[5/7] Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found"
    echo "Please create .env file with required configuration"
    exit 1
fi
echo ".env file found"
echo ""

# Check MySQL/MariaDB service
echo "[6/7] Checking database service..."
if command -v systemctl &> /dev/null; then
    # SystemD-based system
    if systemctl is-active --quiet mysql; then
        echo "MySQL service is running"
    elif systemctl is-active --quiet mariadb; then
        echo "MariaDB service is running"
    else
        echo "WARNING: Database service not running"
        echo "Attempting to start MySQL/MariaDB..."
        sudo systemctl start mysql 2>/dev/null || sudo systemctl start mariadb 2>/dev/null
        if [ $? -ne 0 ]; then
            echo "ERROR: Could not start database service"
            echo "Please start MySQL/MariaDB manually"
            exit 1
        fi
    fi
elif command -v service &> /dev/null; then
    # SysV init system
    if service mysql status &>/dev/null; then
        echo "MySQL service is running"
    else
        echo "WARNING: MySQL service not running"
        echo "Please start MySQL manually: sudo service mysql start"
        exit 1
    fi
else
    echo "WARNING: Cannot detect service manager"
    echo "Please ensure MySQL/MariaDB is running"
fi
echo ""

# Test database connection
echo "[7/7] Testing database connection..."
python -c "from app_v3 import app, db; app.app_context().push(); db.engine.connect(); print('Database connection: OK')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Cannot connect to database"
    echo "Please check your database credentials in .env file"
    exit 1
fi
echo ""

# Check for existing process
echo "Checking for running instances..."
if pgrep -f "python.*app_v3.py" > /dev/null; then
    echo "WARNING: Application may already be running"
    echo "PID(s): $(pgrep -f 'python.*app_v3.py')"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Start the application
echo "========================================"
echo "Starting EZWAI SMM V3.0..."
echo "========================================"
echo ""
echo "Application will be available at:"
echo "  http://localhost:5000"
echo "  http://127.0.0.1:5000"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

python app_v3.py

# Cleanup on exit
deactivate
echo ""
echo "========================================"
echo "Application stopped"
echo "========================================"