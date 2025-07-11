# PowerShell script to start Celery worker for MorningStarBot3
# Usage: .\scripts\celery-worker.ps1

Write-Host "🚀 Starting Celery worker for MorningStarBot3..." -ForegroundColor Green

# Check if Redis is running
try {
    $redisStatus = docker ps --filter "name=morningstar_redis" --format "table {{.Status}}" | Select-String "Up"
    if ($redisStatus) {
        Write-Host "✅ Redis is running" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis is not running. Starting Redis first..." -ForegroundColor Red
        & ".\scripts\redis-start.ps1"
    }
} catch {
    Write-Host "❌ Cannot check Redis status. Make sure Docker is running." -ForegroundColor Red
    exit 1
}

# Change to ai_services directory
Write-Host "📁 Changing to ai_services directory..." -ForegroundColor Yellow
Set-Location -Path "ai_services"

# Start Celery worker
Write-Host "🔧 Starting Celery worker..." -ForegroundColor Yellow
Write-Host "💡 Worker will process tasks from queues: default, categorization, summarization, orchestration, test" -ForegroundColor Cyan
Write-Host "💡 Press Ctrl+C to stop the worker" -ForegroundColor Cyan
Write-Host ""

# Start worker with all queues
try {
    celery -A celery_app worker --loglevel=info --queues=default,categorization,summarization,orchestration,test --hostname=worker1@%h
} catch {
    Write-Host "❌ Failed to start Celery worker: $_" -ForegroundColor Red
    Write-Host "💡 Make sure you're in the ai_services directory and all dependencies are installed" -ForegroundColor Yellow
    Set-Location -Path ".."
    exit 1
} 