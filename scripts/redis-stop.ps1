# PowerShell script to stop Redis for MorningStarBot3
# Usage: .\scripts\redis-stop.ps1

Write-Host "🛑 Stopping Redis infrastructure for MorningStarBot3..." -ForegroundColor Yellow

# Stop containers
docker-compose down redis flower

Write-Host "✅ Redis infrastructure stopped." -ForegroundColor Green
Write-Host ""
Write-Host "📊 Flower dashboard: STOPPED" -ForegroundColor Red
Write-Host "🔧 Redis connection: STOPPED" -ForegroundColor Red
Write-Host ""
Write-Host "💾 Data persisted in Docker volumes:" -ForegroundColor Cyan
Write-Host "  - redis_data (Redis database)" -ForegroundColor White 