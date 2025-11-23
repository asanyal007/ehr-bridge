#!/bin/bash

echo "===================================="
echo " EHR Bridge - Local Development"
echo "===================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed!"
    echo "Please install Python 3.10+ from https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo

# Check if MongoDB is running
echo "Checking MongoDB..."
if ! docker ps | grep -q ehr-mongodb-dev; then
    echo "Starting MongoDB in Docker..."
    docker run -d --name ehr-mongodb-dev -p 27017:27017 -e MONGO_INITDB_DATABASE=ehr mongo:7.0
    sleep 3
fi

echo "✅ MongoDB running on localhost:27017"
echo

# Set environment variables
export JWT_SECRET_KEY="local-dev-secret-key"
export DATABASE_PATH="data/interop.db"
export MONGO_HOST="localhost"
export MONGO_PORT="27017"
export MONGO_DB="ehr"
export PYTHONUNBUFFERED="1"

echo "Installing/updating dependencies..."
cd backend
pip3 install -q -r ../requirements.txt

echo
echo "===================================="
echo " Starting Backend Server"
echo "===================================="
echo
echo "Backend will run on: http://localhost:8000"
echo "Frontend (built) will be served automatically"
echo
echo "Press Ctrl+C to stop the server"
echo

# Run the backend with auto-reload
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000



