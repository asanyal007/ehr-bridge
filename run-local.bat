@echo off
echo ====================================
echo  EHR Bridge - Local Development
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if MongoDB is running
echo Checking MongoDB...
docker ps | findstr ehr-mongodb-dev >nul 2>&1
if errorlevel 1 (
    echo Starting MongoDB in Docker...
    docker run -d --name ehr-mongodb-dev -p 27017:27017 -e MONGO_INITDB_DATABASE=ehr mongo:7.0
    timeout /t 3 >nul
)

echo ✅ MongoDB running on localhost:27017
echo.

REM Set environment variables
set JWT_SECRET_KEY=local-dev-secret-key
set DATABASE_PATH=data/interop.db
set MONGO_HOST=localhost
set MONGO_PORT=27017
set MONGO_DB=ehr
set PYTHONUNBUFFERED=1

echo Installing/updating dependencies...
cd backend
pip install -q -r ../requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies
    echo Try running: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo ====================================
echo  Starting Backend Server
echo ====================================
echo.
echo Backend will run on: http://localhost:8000
echo Frontend (built) will be served automatically
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the backend with auto-reload
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000



