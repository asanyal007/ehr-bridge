# EHR AI Data Interoperability Platform - Windows PowerShell Startup Script

# Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     EHR AI Data Interoperability Platform - Windows Deployment              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Function to check command existence
function Test-Command {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) {
            return $true
        }
    }
    catch {
        return $false
    }
}

# Check Docker Desktop installation
Write-Host "[1/6] Checking Docker Desktop installation..." -ForegroundColor Yellow
if (-not (Test-Command "docker")) {
    Write-Host "❌ Docker Desktop is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Docker Desktop from:" -ForegroundColor White
    Write-Host "https://www.docker.com/products/docker-desktop" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✅ Docker Desktop found" -ForegroundColor Green

# Check if Docker is running
Write-Host "[2/6] Checking if Docker Desktop is running..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✅ Docker Desktop is running" -ForegroundColor Green
}
catch {
    Write-Host "❌ Docker Desktop is not running" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Create necessary directories
Write-Host "[3/6] Creating data directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\data" | Out-Null
Write-Host "✅ Directories created" -ForegroundColor Green

# Check for .env file
Write-Host "[4/6] Checking environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  No .env file found. Creating from template..." -ForegroundColor Yellow
    $envContent = @"
# EHR Platform Environment Configuration
# Generated on $(Get-Date)

# JWT Secret Key for authentication
JWT_SECRET_KEY=change-this-to-a-secure-random-string

# Google Gemini API Key for AI features
# Get your key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your-gemini-api-key-here

# MongoDB Configuration
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DB=ehr
"@
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ Created .env file - Please edit with your API keys" -ForegroundColor Green
    notepad .env
}
Write-Host "✅ Environment configured" -ForegroundColor Green

# Stop any existing containers
Write-Host "[5/6] Stopping existing containers..." -ForegroundColor Yellow
docker-compose down 2>&1 | Out-Null
Write-Host "✅ Cleaned up existing containers" -ForegroundColor Green

# Start the application
Write-Host "[6/6] Starting EHR Platform..." -ForegroundColor Yellow
Write-Host ""
Write-Host "This may take a few minutes on first run (downloading images and models)..." -ForegroundColor Cyan
Write-Host ""

docker-compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Failed to start the application" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check the error messages above." -ForegroundColor White
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                          🚀 DEPLOYMENT SUCCESSFUL!                           ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "The EHR AI Data Interoperability Platform is now running!" -ForegroundColor White
Write-Host ""
Write-Host "📊 Application URL:    http://localhost:8000" -ForegroundColor Cyan
Write-Host "📊 Alternative URL:    http://localhost:3000" -ForegroundColor Cyan
Write-Host "🗄️  MongoDB:            mongodb://localhost:27017" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view logs:          docker-compose logs -f" -ForegroundColor Yellow
Write-Host "To stop:               docker-compose down" -ForegroundColor Yellow
Write-Host "To restart:            docker-compose restart" -ForegroundColor Yellow
Write-Host ""
Write-Host "Opening application in browser..." -ForegroundColor White
Start-Sleep -Seconds 5
Start-Process "http://localhost:8000"
Write-Host ""
Read-Host "Press Enter to exit"

