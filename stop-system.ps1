#!/usr/bin/env pwsh
# MorningStarBot3 - Остановка системы
# Запуск: .\stop-system.ps1

Write-Host "🛑 Остановка MorningStarBot3 системы..." -ForegroundColor Yellow

# Остановка всех связанных процессов
try {
    # Остановка N8N процессов
    Write-Host "🔗 Остановка N8N..." -ForegroundColor Cyan
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { 
        $_.ProcessName -eq "node" -and ($_.CommandLine -like "*n8n*" -or $_.CommandLine -like "*5678*")
    } | ForEach-Object {
        Write-Host "   Остановка PID: $($_.Id)" -ForegroundColor Gray
        $_.Kill()
    }

    # Остановка Backend процессов
    Write-Host "🔧 Остановка Backend..." -ForegroundColor Cyan
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { 
        $_.CommandLine -like "*backend*" -or $_.CommandLine -like "*main.py*"
    } | ForEach-Object {
        Write-Host "   Остановка PID: $($_.Id)" -ForegroundColor Gray
        $_.Kill()
    }

    # Остановка Userbot процессов
    Write-Host "🤖 Остановка Userbot..." -ForegroundColor Cyan
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { 
        $_.CommandLine -like "*userbot*" -or $_.CommandLine -like "*bot.py*"
    } | ForEach-Object {
        Write-Host "   Остановка PID: $($_.Id)" -ForegroundColor Gray
        $_.Kill()
    }

    # Освобождение портов принудительно
    Write-Host "🔌 Освобождение портов..." -ForegroundColor Cyan
    
    # Порт 8000 (Backend)
    netstat -ano | findstr :8000 | ForEach-Object { 
        $pid = ($_ -split '\s+')[-1]
        if ($pid -match '^\d+$') {
            Write-Host "   Освобождение порта 8000 (PID: $pid)" -ForegroundColor Gray
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
    }
    
    # Порт 5678 (N8N)  
    netstat -ano | findstr :5678 | ForEach-Object { 
        $pid = ($_ -split '\s+')[-1]
        if ($pid -match '^\d+$') {
            Write-Host "   Освобождение порта 5678 (PID: $pid)" -ForegroundColor Gray
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
    }

    Start-Sleep 2

    # Проверка что порты освобождены
    $port8000 = Test-NetConnection -ComputerName localhost -Port 8000 -InformationLevel Quiet -WarningAction SilentlyContinue
    $port5678 = Test-NetConnection -ComputerName localhost -Port 5678 -InformationLevel Quiet -WarningAction SilentlyContinue

    Write-Host "`n📊 Статус портов:" -ForegroundColor White
    Write-Host "   • Порт 8000 (Backend): $(if(-not $port8000){'✅ Свободен'}else{'❌ Занят'})" -ForegroundColor $(if(-not $port8000){'Green'}else{'Red'})
    Write-Host "   • Порт 5678 (N8N): $(if(-not $port5678){'✅ Свободен'}else{'❌ Занят'})" -ForegroundColor $(if(-not $port5678){'Green'}else{'Red'})

    Write-Host "`n🏁 Система MorningStarBot3 остановлена!" -ForegroundColor Green

} catch {
    Write-Host "❌ Ошибка при остановке: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Попробуйте перезапустить PowerShell от имени администратора" -ForegroundColor Yellow
}

Write-Host "`n🚀 Для запуска системы: .\start-system.ps1" -ForegroundColor Cyan 