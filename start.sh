#!/bin/bash

# ============================================================================
# EHR AI Data Interoperability Platform - macOS Startup Script
# ============================================================================

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║     EHR AI Data Interoperability Platform - macOS Deployment                ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker Desktop is installed
echo "[1/6] Checking Docker Desktop installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker Desktop is not installed or not in PATH"
    echo ""
    echo "Please install Docker Desktop from:"
    echo "https://www.docker.com/products/docker-desktop"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi
echo "✅ Docker Desktop found"

# Check if Docker is running
echo "[2/6] Checking if Docker Desktop is running..."
if ! docker ps &> /dev/null; then
    echo "❌ Docker Desktop is not running"
    echo ""
    echo "Please start Docker Desktop and try again."
    echo "You can start it from Applications or use:"
    echo "  open -a Docker"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi
echo "✅ Docker Desktop is running"

# Create necessary directories
echo "[3/6] Creating data directories..."
mkdir -p data
mkdir -p backend/data
echo "✅ Directories created"

# Check for .env file
echo "[4/6] Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cat > .env << 'EOF'
# EHR Platform Environment Configuration
# Generated on $(date)

# JWT Secret Key for authentication
JWT_SECRET_KEY=change-this-to-a-secure-random-string

# Google Gemini API Key for AI features
# Get your key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your-gemini-api-key-here

# MongoDB Configuration
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DB=ehr
EOF
    echo "✅ Created .env file - Please edit with your API keys"
    
    # Open .env file in default editor
    if command -v nano &> /dev/null; then
        echo "Opening .env in nano editor..."
        nano .env
    elif command -v vim &> /dev/null; then
        echo "Opening .env in vim editor..."
        vim .env
    else
        echo "Please edit .env file manually with your API keys"
        read -p "Press Enter when done..."
    fi
fi
echo "✅ Environment configured"

# Stop any existing containers
echo "[5/6] Stopping existing containers..."
docker-compose down &> /dev/null || true
echo "✅ Cleaned up existing containers"

# Start the application
echo "[6/6] Starting EHR Platform..."
echo ""
echo "This may take a few minutes on first run (downloading images and models)..."
echo ""

if docker-compose up -d --build; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                          🚀 DEPLOYMENT SUCCESSFUL!                           ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "The EHR AI Data Interoperability Platform is now running!"
    echo ""
    echo "📊 Application URL:    http://localhost:8000"
    echo "📊 Alternative URL:    http://localhost:3000"
    echo "🗄️  MongoDB:            mongodb://localhost:27017"
    echo ""
    echo "To view logs:          docker-compose logs -f"
    echo "To stop:               docker-compose down"
    echo "To restart:            docker-compose restart"
    echo ""
    echo "Opening application in browser..."
    sleep 5
    open http://localhost:8000
    echo ""
    echo "Press Enter to exit..."
    read
else
    echo ""
    echo "❌ Failed to start the application"
    echo ""
    echo "Please check the error messages above."
    read -p "Press Enter to exit..."
    exit 1
fi

