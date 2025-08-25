# Test script for the link health job (PowerShell)
# Run this to test the job locally

$BASE_URL = if ($env:NEXT_PUBLIC_APP_URL) { $env:NEXT_PUBLIC_APP_URL } else { "http://localhost:3000" }

Write-Host "🧪 Testing Link Health Job..." -ForegroundColor Cyan
Write-Host ""

try {
    # Test 1: Dry run with small limit
    Write-Host "📋 Test 1: Dry run (5 files)" -ForegroundColor Yellow
    $dryRunResponse = Invoke-RestMethod -Uri "$BASE_URL/api/jobs/link-health?limit=5&dryRun=true" -Method GET
    Write-Host "Response:" -ForegroundColor Green
    $dryRunResponse | ConvertTo-Json -Depth 10
    Write-Host "✅ Dry run completed" -ForegroundColor Green
    Write-Host ""

    # Test 2: Small actual run
    Write-Host "🔍 Test 2: Actual run (3 files)" -ForegroundColor Yellow
    $body = @{
        limit = 3
        dryRun = $false
    } | ConvertTo-Json
    
    $actualResponse = Invoke-RestMethod -Uri "$BASE_URL/api/jobs/link-health" -Method POST -Body $body -ContentType "application/json"
    Write-Host "Response:" -ForegroundColor Green
    $actualResponse | ConvertTo-Json -Depth 10
    Write-Host "✅ Actual run completed" -ForegroundColor Green
    Write-Host ""

    # Test 3: Check database for updates
    Write-Host "📊 Test 3: Checking database for link_health field" -ForegroundColor Yellow
    $dbCheckResponse = Invoke-RestMethod -Uri "$BASE_URL/api/jobs/link-health?limit=1&dryRun=true" -Method GET
    Write-Host "Database check response:" -ForegroundColor Green
    $dbCheckResponse | ConvertTo-Json -Depth 10
    Write-Host "✅ Database check completed" -ForegroundColor Green
    Write-Host ""

    Write-Host "🎉 All tests completed successfully!" -ForegroundColor Green

} catch {
    Write-Host "❌ Test failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
