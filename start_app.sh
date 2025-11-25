#!/bin/bash

# Function to kill background processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    # Kill all child processes in the current process group
    kill 0
    exit
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM EXIT

echo "========================================"
echo "🚀 Starting AutoFX App Setup & Launch"
echo "========================================"

# 1. Check Node.js
if ! command -v npm &> /dev/null; then
    echo "❌ Error: Node.js (npm) is not installed."
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# 2. Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed."
    echo "Please install Python 3."
    exit 1
fi

# 3. Install Node Dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install Node dependencies."
        exit 1
    fi
else
    echo "✅ Node dependencies found."
fi

# 4. Setup Python Virtual Environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
    
    echo "📦 Installing Python requirements..."
    ./venv/bin/pip install -r backend/requirements.txt
    
    echo "🎭 Installing Playwright browsers..."
    ./venv/bin/playwright install chromium
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to setup Python environment."
        exit 1
    fi
else
    echo "✅ Python virtual environment found."
fi

echo "========================================"
echo "🔥 Starting Servers..."
echo "========================================"

# 5. Start Backend
echo "Starting Backend Server (Port 3001)..."
npm run server &

# Wait a bit for backend to initialize
sleep 3

# 6. Start Frontend
echo "Starting Frontend (Port 5173)..."
npm run dev &

echo "========================================"
echo "✅ App is running!"
echo "👉 Access the app at: http://localhost:5173"
echo "========================================"
echo "Press Ctrl+C to stop everything."

# Wait for any process to exit
wait
