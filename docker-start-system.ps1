#!/usr/bin/env pwsh
# Скрипт для запуска полной Docker системы MorningStarBot3

Write-Host "🚀 Запуск полной Docker системы MorningStarBot3..." -ForegroundColor Green
Write-Host "=" * 60

# Проверяем наличие docker-compose
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ docker-compose не найден! Установите Docker Desktop." -ForegroundColor Red
    exit 1
}

# Проверяем наличие .env файла
if (-not (Test-Path ".env")) {
    Write-Host "⚠️ Файл .env не найден. Создайте его на основе env-example.txt" -ForegroundColor Yellow
    if (Test-Path "env-example.txt") {
        Write-Host "📋 Пример найден в env-example.txt" -ForegroundColor Yellow
    }
    exit 1
}

Write-Host "🔧 Построение Docker образов..." -ForegroundColor Yellow
docker-compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка построения Docker образов!" -ForegroundColor Red
    exit 1
}

Write-Host "🚀 Запуск всех сервисов..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка запуска сервисов!" -ForegroundColor Red
    exit 1
}

Write-Host "⏳ Ожидание инициализации сервисов..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "🔍 Проверка статуса сервисов..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "✅ Система запущена! Доступные сервисы:" -ForegroundColor Green
Write-Host "🌐 Frontend (Admin Panel): http://localhost:80" -ForegroundColor Cyan
Write-Host "🔧 Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📊 Flower Dashboard: http://localhost:5555" -ForegroundColor Cyan
Write-Host "🤖 PublicBot: Интегрирован в Docker сеть" -ForegroundColor Cyan
Write-Host "🗄️ PostgreSQL: localhost:5432" -ForegroundColor Cyan
Write-Host "🔴 Redis: localhost:6379" -ForegroundColor Cyan

Write-Host ""
Write-Host "📋 Полезные команды:" -ForegroundColor Yellow
Write-Host "docker-compose logs -f [service]  # Просмотр логов"
Write-Host "docker-compose stop             # Остановка системы"
Write-Host "docker-compose down             # Остановка и удаление контейнеров"
Write-Host "python temp/test_docker_architecture.py  # Тестирование системы"

Write-Host ""
Write-Host "🔗 Мультитенантность PublicBot:" -ForegroundColor Yellow
Write-Host "docker-compose up -d --scale publicbot=3  # Масштабирование одного бота"
Write-Host "docker-compose -f docker-compose.yml -f docker-compose.multitenant.yml up -d  # Разные боты"

Write-Host ""
Write-Host "🎯 Для тестирования запустите:" -ForegroundColor Green
Write-Host "python temp/test_docker_architecture.py" -ForegroundColor Cyan 