Write-Host "🔄 Restarting Backend..." -ForegroundColor Cyan

# Step 1: Kill all Python processes
Write-Host "1️⃣ Stopping all Python processes..." -ForegroundColor Yellow
taskkill /F /IM python.exe 2>$null
Start-Sleep -Seconds 1

# Step 2: Start backend fresh
Write-Host "2️⃣ Starting backend on port 8002..." -ForegroundColor Yellow
Start-Process -FilePath "cmd" -ArgumentList "/k .\venv\Scripts\python.exe backend/run.py" -WindowStyle Normal

# Step 3: Wait for startup
Write-Host "3️⃣ Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Step 4: Test health endpoint
Write-Host "4️⃣ Testing health endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8002/api/v1/health" -Method GET
    Write-Host "✅ Backend is healthy!" -ForegroundColor Green
    Write-Host "   Status: $($health.status)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Backend health check failed!" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 5: Check if new endpoint exists
Write-Host "5️⃣ Checking if /get-suggestion endpoint is registered..." -ForegroundColor Yellow
try {
    $openapi = Invoke-RestMethod -Uri "http://localhost:8002/openapi.json" -Method GET
    $paths = $openapi.paths.PSObject.Properties.Name
    
    if ($paths -like "*get-suggestion*") {
        Write-Host "✅ Endpoint /get-suggestion is registered!" -ForegroundColor Green
        Write-Host "" 
        Write-Host "🎉 All done! You can now:" -ForegroundColor Cyan
        Write-Host "   1. Visit http://localhost:8002/docs to see all endpoints" -ForegroundColor Gray
        Write-Host "   2. Try the 'Get AI Suggestion' button in your UI" -ForegroundColor Gray
        Write-Host "   3. Make sure LM Studio is running on http://localhost:1234" -ForegroundColor Gray
    } else {
        Write-Host "❌ Endpoint /get-suggestion NOT found!" -ForegroundColor Red
        Write-Host "   Available paths:" -ForegroundColor Yellow
        $paths | Where-Object { $_ -like "*jobs*" } | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }
    }
} catch {
    Write-Host "⚠️ Could not check OpenAPI schema" -ForegroundColor Yellow
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
