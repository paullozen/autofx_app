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
    echo.
    echo We can try to install it automatically using Winget.
    choice /M "Do you want to install Node.js now?"
    if errorlevel 1 (
        echo 📦 Installing Node.js...
        winget install -e --id OpenJS.NodeJS
        if %errorlevel% neq 0 (
            echo ❌ Installation failed. Opening download page...
            start https://nodejs.org/
        ) else (
            echo ✅ Node.js installed!
            echo ⚠️  Please RESTART this script to apply changes.
            pause
            exit /b
        )
    ) else (
        echo Opening download page...
        start https://nodejs.org/
    )
    pause
    exit /b 1
)

:: 2. Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error: Python is not installed.
    echo.
    echo We can try to install it automatically using Winget.
    choice /M "Do you want to install Python 3 now?"
    if errorlevel 1 (
        echo 📦 Installing Python 3...
        winget install -e --id Python.Python.3.11
        if %errorlevel% neq 0 (
            echo ❌ Installation failed. Opening download page...
            start https://www.python.org/downloads/
        ) else (
            echo ✅ Python installed!
            echo ⚠️  Please RESTART this script to apply changes.
            pause
            exit /b
        )
    ) else (
        echo Opening download page...
        start https://www.python.org/downloads/
    )
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
