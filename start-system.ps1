#!/usr/bin/env pwsh
# MorningStarBot3 - Автоматический запуск всей системы
# Запуск: .\start-system.ps1

Write-Host "🚀 Запуск MorningStarBot3 системы..." -ForegroundColor Green

# Проверка что мы в правильной директории
if (-not (Test-Path "backend") -or -not (Test-Path "userbot")) {
    Write-Host "❌ Запустите скрипт из корня проекта MorningStarBot3" -ForegroundColor Red
    exit 1
}

# Функция для проверки что порт свободен
function Test-Port($port) {
    $connection = Test-NetConnection -ComputerName localhost -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue
    return -not $connection
}

# Функция для ожидания запуска сервиса
function Wait-ForService($name, $url, $timeout = 30) {
    Write-Host "⏳ Ожидание запуска $name..." -ForegroundColor Yellow
    $count = 0
    do {
        Start-Sleep 2
        $count += 2
        try {
            $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 5 2>$null
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ $name запущен!" -ForegroundColor Green
                return $true
            }
        } catch {
            # Продолжаем ожидание
        }
    } while ($count -lt $timeout)
    
    Write-Host "❌ $name не запустился за $timeout секунд" -ForegroundColor Red
    return $false
}

# Остановка предыдущих процессов
Write-Host "🛑 Остановка предыдущих процессов..." -ForegroundColor Yellow
Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -eq "node" } | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*backend*" -or $_.CommandLine -like "*bot.py*" } | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep 3

try {
    # 1. Запуск Backend API
    Write-Host "🔧 Запуск Backend API..." -ForegroundColor Cyan
    if (-not (Test-Port 8000)) {
        Write-Host "⚠️ Порт 8000 занят, попытка освободить..." -ForegroundColor Yellow
        netstat -ano | findstr :8000 | ForEach-Object { 
            $processId = ($_ -split '\s+')[-1]
            if ($processId -match '^\d+$') {
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            }
        }
        Start-Sleep 2
    }
    
    $backendProcess = Start-Process -FilePath "python" -ArgumentList "backend/main.py" -WindowStyle Hidden -PassThru
    Write-Host "📋 Backend PID: $($backendProcess.Id)" -ForegroundColor Gray
    
    # Ждем запуска Backend
    if (-not (Wait-ForService "Backend API" "http://localhost:8000/api/channels")) {
        throw "Backend API не запустился"
    }

    # 2. Запуск N8N
    Write-Host "🔗 Запуск N8N..." -ForegroundColor Cyan
    if (-not (Test-Port 5678)) {
        Write-Host "⚠️ Порт 5678 занят, попытка освободить..." -ForegroundColor Yellow
        netstat -ano | findstr :5678 | ForEach-Object { 
            $processId = ($_ -split '\s+')[-1]
            if ($processId -match '^\d+$') {
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            }
        }
        Start-Sleep 2
    }
    
    $n8nProcess = Start-Process -FilePath "npx" -ArgumentList "n8n", "start", "--tunnel" -WindowStyle Hidden -PassThru
    Write-Host "📋 N8N PID: $($n8nProcess.Id)" -ForegroundColor Gray
    
    # Ждем запуска N8N
    if (-not (Wait-ForService "N8N" "http://localhost:5678/healthz")) {
        throw "N8N не запустился"
    }

    # 3. Автоматический импорт workflow
    Write-Host "📦 Импорт N8N workflow..." -ForegroundColor Cyan
    Start-Sleep 5  # Дополнительное время для полной инициализации N8N
    
    # Попытка импорта workflow через API
    try {
        $workflowPath = "n8n/workflows/telegram-digest-workflow.json"
        if (Test-Path $workflowPath) {
            $workflowContent = Get-Content $workflowPath -Raw | ConvertFrom-Json
            $importPayload = @{
                "workflow" = $workflowContent
            } | ConvertTo-Json -Depth 20
            
            $headers = @{
                "Content-Type" = "application/json"
            }
            
            # Импорт workflow
            $importResponse = Invoke-RestMethod -Uri "http://localhost:5678/rest/workflows/import" -Method POST -Body $importPayload -Headers $headers
            Write-Host "✅ Workflow импортирован: $($importResponse.name)" -ForegroundColor Green
            
            # Активация workflow
            if ($importResponse.id) {
                $activatePayload = @{ "active" = $true } | ConvertTo-Json
                Invoke-RestMethod -Uri "http://localhost:5678/rest/workflows/$($importResponse.id)/activate" -Method POST -Body $activatePayload -Headers $headers
                Write-Host "✅ Workflow активирован!" -ForegroundColor Green
            }
        } else {
            Write-Host "⚠️ Workflow файл не найден: $workflowPath" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️ Автоматический импорт не удался, импортируйте вручную через http://localhost:5678" -ForegroundColor Yellow
        Write-Host "   Файл: n8n/workflows/telegram-digest-workflow.json" -ForegroundColor Gray
    }

    # 4. Информация о запущенной системе
    Write-Host "`n🎉 Система MorningStarBot3 запущена!" -ForegroundColor Green
    Write-Host "📋 Процессы:" -ForegroundColor White
    Write-Host "   • Backend API: http://localhost:8000 (PID: $($backendProcess.Id))" -ForegroundColor Gray
    Write-Host "   • N8N: http://localhost:5678 (PID: $($n8nProcess.Id))" -ForegroundColor Gray
    Write-Host "   • Admin Panel: http://localhost:3000 (запустите отдельно)" -ForegroundColor Gray
    
    Write-Host "`n🔧 Управление:" -ForegroundColor White
    Write-Host "   • Запуск Userbot: cd userbot && python src/bot.py" -ForegroundColor Gray
    Write-Host "   • Остановка: .\stop-system.ps1" -ForegroundColor Gray
    Write-Host "   • Логи N8N: Ctrl+C для остановки" -ForegroundColor Gray
    
    Write-Host "`n✅ Готово к работе!" -ForegroundColor Green
    Write-Host "Нажмите Ctrl+C для остановки системы..." -ForegroundColor Yellow
    
    # Ожидание прерывания
    try {
        while ($true) {
            Start-Sleep 1
            # Проверяем что процессы еще живы
            if ($backendProcess.HasExited) {
                Write-Host "❌ Backend процесс завершился" -ForegroundColor Red
                break
            }
            if ($n8nProcess.HasExited) {
                Write-Host "❌ N8N процесс завершился" -ForegroundColor Red
                break
            }
        }
    } catch {
        Write-Host "`n🛑 Получен сигнал остановки..." -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ Ошибка запуска: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    # Остановка процессов
    Write-Host "`n🛑 Остановка системы..." -ForegroundColor Yellow
    
    if ($backendProcess -and -not $backendProcess.HasExited) {
        $backendProcess.Kill()
        Write-Host "   ✅ Backend остановлен" -ForegroundColor Gray
    }
    
    if ($n8nProcess -and -not $n8nProcess.HasExited) {
        $n8nProcess.Kill()
        Write-Host "   ✅ N8N остановлен" -ForegroundColor Gray
    }
    
    Write-Host "🏁 Система остановлена." -ForegroundColor Green
} 