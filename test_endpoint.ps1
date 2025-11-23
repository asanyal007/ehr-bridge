$body = @{
    sourceField = "test_field"
    sourceType = "string"
    targetField = "Patient.name"
    confidence = 0.3
    targetResourceType = "Patient"
} | ConvertTo-Json

$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer demo_token"
}

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8002/api/v1/jobs/test123/get-suggestion" -Method Post -Body $body -Headers $headers
    Write-Host "Success!" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
}
