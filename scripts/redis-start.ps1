# PowerShell script to start Redis for MorningStarBot3
# Usage: .\scripts\redis-start.ps1

Write-Host "🚀 Starting Redis infrastructure for MorningStarBot3..." -ForegroundColor Green

# Check if Docker is running
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Start Redis and Flower
Write-Host "🐳 Starting Redis and Flower containers..." -ForegroundColor Yellow
docker-compose up -d redis flower

# Wait for Redis to be ready
Write-Host "⏳ Waiting for Redis to be ready..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0

do {
    $attempt++
    Start-Sleep -Seconds 2
    
    try {
        $result = docker exec morningstar_redis redis-cli ping
        if ($result -eq "PONG") {
            Write-Host "✅ Redis is ready!" -ForegroundColor Green
            break
        }
    } catch {
        # Continue trying
    }
    
    if ($attempt -eq $maxAttempts) {
        Write-Host "❌ Redis failed to start after $maxAttempts attempts" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "🔄 Attempt $attempt/$maxAttempts - Redis starting..." -ForegroundColor Yellow
} while ($true)

# Check Flower
Write-Host "🌸 Checking Flower dashboard..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

try {
    $response = Invoke-WebRequest -Uri "http://localhost:5555" -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Flower dashboard is ready at http://localhost:5555" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ Flower dashboard may still be starting. Check http://localhost:5555 in a few moments." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Redis infrastructure is ready!" -ForegroundColor Green
Write-Host "📊 Flower dashboard: http://localhost:5555" -ForegroundColor Cyan
Write-Host "🔧 Redis connection: localhost:6379" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Test Redis connection with Python" -ForegroundColor White
Write-Host "2. Install Celery dependencies" -ForegroundColor White
Write-Host "3. Create Celery app configuration" -ForegroundColor White 