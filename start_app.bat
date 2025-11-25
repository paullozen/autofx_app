@echo off
setlocal
title AutoFX App Launcher

echo ========================================
echo 🚀 Starting AutoFX App Setup & Launch
echo ========================================

:: 1. Check Node.js
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error: Node.js is not installed.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

:: 2. Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error: Python is not installed.
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

:: 3. Install Node Dependencies
if not exist "node_modules" (
    echo 📦 Installing Node.js dependencies...
    call npm install
    if %errorlevel% neq 0 (
        echo ❌ Failed to install Node dependencies.
        pause
        exit /b 1
    )
) else (
    echo ✅ Node dependencies found.
)

:: 4. Setup Python Virtual Environment
if not exist "venv" (
    echo 🐍 Creating Python virtual environment...
    python -m venv venv
    
    echo 📦 Installing Python requirements...
    call venv\Scripts\pip install -r backend\requirements.txt
    
    echo 🎭 Installing Playwright browsers...
    call venv\Scripts\playwright install chromium
    
    if %errorlevel% neq 0 (
        echo ❌ Failed to setup Python environment.
        pause
        exit /b 1
    )
) else (
    echo ✅ Python virtual environment found.
)

echo ========================================
echo 🔥 Starting Servers...
echo ========================================

:: 5. Start Backend
echo Starting Backend Server...
start "AutoFX Backend" cmd /c "npm run server"

:: 6. Start Frontend
echo Starting Frontend...
start "AutoFX Frontend" cmd /c "npm run dev"

echo ========================================
echo ✅ App is running!
echo 👉 Access the app at: http://localhost:5173
echo ========================================
echo.
echo The servers are running in separate windows.
echo Close those windows to stop the application.
pause
