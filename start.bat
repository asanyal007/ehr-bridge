@echo off
SETLOCAL EnableDelayedExpansion

REM ============================================================================
REM EHR AI Data Interoperability Platform - Windows Startup Script
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║     EHR AI Data Interoperability Platform - Windows Deployment              ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

REM Check if Docker Desktop is installed
echo [1/6] Checking Docker Desktop installation...
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker Desktop is not installed or not in PATH
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)
echo ✅ Docker Desktop found

REM Check if Docker is running
echo [2/6] Checking if Docker Desktop is running...
docker ps >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker Desktop is not running
    echo.
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)
echo ✅ Docker Desktop is running

REM Create necessary directories
echo [3/6] Creating data directories...
if not exist "data" mkdir data
if not exist "backend\data" mkdir backend\data
echo ✅ Directories created

REM Check for .env file
echo [4/6] Checking environment configuration...
if not exist ".env" (
    echo ⚠️  No .env file found. Creating from template...
    (
        echo # EHR Platform Environment Configuration
        echo # Generated on %date% %time%
        echo.
        echo # JWT Secret Key for authentication
        echo JWT_SECRET_KEY=change-this-to-a-secure-random-string
        echo.
        echo # Google Gemini API Key for AI features
        echo # Get your key from: https://makersuite.google.com/app/apikey
        echo GEMINI_API_KEY=your-gemini-api-key-here
        echo.
        echo # MongoDB Configuration
        echo MONGO_HOST=mongodb
        echo MONGO_PORT=27017
        echo MONGO_DB=ehr
    ) > .env
    echo ✅ Created .env file - Please edit with your API keys
    notepad .env
)
echo ✅ Environment configured

REM Stop any existing containers
echo [5/6] Stopping existing containers...
docker-compose down >nul 2>&1
echo ✅ Cleaned up existing containers

REM Start the application
echo [6/6] Starting EHR Platform...
echo.
echo This may take a few minutes on first run (downloading images and models)...
echo.

docker-compose up -d --build

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Failed to start the application
    echo.
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                          🚀 DEPLOYMENT SUCCESSFUL!                           ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.
echo The EHR AI Data Interoperability Platform is now running!
echo.
echo 📊 Application URL:    http://localhost:8000
echo 📊 Alternative URL:    http://localhost:3000
echo 🗄️  MongoDB:            mongodb://localhost:27017
echo.
echo To view logs:          docker-compose logs -f
echo To stop:               docker-compose down
echo To restart:            docker-compose restart
echo.
echo Opening application in browser...
timeout /t 5 /nobreak >nul
start http://localhost:8000
echo.
echo Press any key to exit...
pause >nul

