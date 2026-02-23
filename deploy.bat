@echo off
REM Automated Deployment Script for Windows
REM This script pulls the latest code from Git and restarts Docker services

echo ========================================
echo    Starting Deployment Process
echo ========================================

REM Check if docker-compose.yml exists
if not exist "docker-compose.yml" (
    echo [Error] docker-compose.yml not found!
    echo Please run this script from the project root directory.
    exit /b 1
)

REM Step 1: Pull latest changes from Git
echo.
echo [1/5] Pulling latest changes from Git...
git fetch origin
git pull origin main
if errorlevel 1 (
    echo [Error] Failed to pull changes from Git
    exit /b 1
)
echo [Success] Code updated successfully

REM Step 2: Check .env file
echo.
echo [2/5] Checking .env file...
if not exist ".env" (
    echo [Error] .env file not found!
    if exist ".env.example" (
        echo Do you want to copy from .env.example? (Y/N)
        set /p REPLY=
        if /i "%REPLY%"=="Y" (
            copy .env.example .env
            echo [Success] .env file created. Please edit it and run deploy again
            exit /b 1
        ) else (
            exit /b 1
        )
    ) else (
        exit /b 1
    )
) else (
    echo [Success] .env file exists
)

REM Step 3: Stop previous services
echo.
echo [3/5] Stopping previous services...
docker compose down
echo [Success] Services stopped

REM Step 4: Build and start new services
echo.
echo [4/5] Building and starting new services...
docker compose build --no-cache
docker compose up -d
if errorlevel 1 (
    echo [Error] Failed to start services
    exit /b 1
)
echo [Success] Services started successfully

REM Step 5: Check service status
echo.
echo [5/5] Checking service status...
timeout /t 5 /nobreak >nul

echo.
echo Container Status:
docker compose ps

echo.
echo Checking Health Endpoint...
timeout /t 10 /nobreak >nul

curl -s -o nul -w "HTTP Status: %%{http_code}" http://localhost:8001/health
echo.

REM Show recent logs
echo.
echo Recent API Logs:
docker compose logs --tail=20 api

echo.
echo ========================================
echo    Deployment Completed Successfully!
echo ========================================

echo.
echo Useful Commands:
echo   • View logs:           docker compose logs -f
echo   • View API logs:       docker compose logs -f api
echo   • View Worker logs:    docker compose logs -f worker
echo   • Service status:      docker compose ps
echo   • Restart services:    docker compose restart
echo   • Stop services:       docker compose down

echo.
echo API is available at:
echo   • Health: http://localhost:8001/health
echo   • Docs:   http://localhost:8001/docs

pause
