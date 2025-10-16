@echo off
title Package Manager - Starting Services

echo.
echo ================================================
echo   Package Manager Startup Script
echo ================================================
echo.

REM Check if requirements.txt exists
if not exist requirements.txt (
    echo [ERROR] requirements.txt not found!
    pause
    exit /b 1
)

echo [1/5] Installing Python requirements...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python requirements
    pause
    exit /b 1
)

echo.
echo [2/5] Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed!
    pause
    exit /b 1
)

echo [3/5] Installing backend dependencies...
cd backend
if not exist node_modules (
    npm install
)
cd ..

echo [4/5] Installing frontend dependencies...
cd frontend
if not exist node_modules (
    npm install
)
cd ..

echo.
echo [5/5] Starting services...
echo   Starting backend
echo   Starting Frontend


REM Start backend in new window
start "Backend Server" cmd /k "cd backend && npm start"

REM Wait 3 seconds for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
start "Frontend Server" cmd /k "cd frontend && npm start"

cls

echo.
echo ================================================
echo   Services Started Successfully!
echo ================================================
echo   Backend
echo   Frontend
echo ================================================
echo.
echo.
echo To stop all services, close the Backend and Frontend windows
echo.
pause
