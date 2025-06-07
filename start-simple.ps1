#!/usr/bin/env pwsh
# MorningStarBot3 - Простой запуск системы

Write-Host "🚀 Запуск MorningStarBot3..." -ForegroundColor Green

try {
    # 1. Запуск Backend API
    Write-Host "🔧 Запуск Backend API на порту 8000..." -ForegroundColor Cyan
    Start-Process -FilePath "python" -ArgumentList "backend/main.py" -WindowStyle Normal -WorkingDirectory $PWD
    Write-Host "✅ Backend запускается..." -ForegroundColor Green
    
    Start-Sleep 5
    
    # 2. Запуск N8N  
    Write-Host "🔗 Запуск N8N на порту 5678..." -ForegroundColor Cyan
    Start-Process -FilePath "npx" -ArgumentList "n8n" -WindowStyle Normal -WorkingDirectory $PWD
    Write-Host "✅ N8N запускается..." -ForegroundColor Green
    
    Write-Host "`n🎉 Система запускается!" -ForegroundColor Green
    Write-Host "📋 Откроются 2 окна:" -ForegroundColor White
    Write-Host "   • Backend API: http://localhost:8000" -ForegroundColor Gray
    Write-Host "   • N8N: http://localhost:5678" -ForegroundColor Gray
    
    Write-Host "`n🔧 Для остановки:" -ForegroundColor Yellow
    Write-Host "   • Закройте оба окна или нажмите Ctrl+C в каждом" -ForegroundColor Gray
    Write-Host "   • Или используйте: .\stop-system.ps1" -ForegroundColor Gray
    
    Write-Host "`n✅ Готово! Подождите 10-15 секунд для полного запуска." -ForegroundColor Green
    
} catch {
    Write-Host "❌ Ошибка запуска: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nНажмите любую клавишу для закрытия..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 