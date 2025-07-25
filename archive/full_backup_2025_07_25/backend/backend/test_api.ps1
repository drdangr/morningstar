# Тестирование Digest API
Write-Host "🧪 Тестирование Digest API endpoints..." -ForegroundColor Green

# 1. Создание тестового дайджеста
$digestData = @{
    digest_id = "test_digest_123"
    total_posts = 4
    channels_processed = 2
    original_posts = 10
    relevant_posts = 4
    avg_importance = 8.0
    avg_urgency = 6.75
    avg_significance = 7.5
    binary_relevance_applied = $true
    with_metrics = $true
    digest_data = '{"channels":[{"title":"Breaking Mash","username":"@breakingmash","posts_count":2}]}'
    processed_at = "2025-12-08T10:00:00Z"
}

$json = $digestData | ConvertTo-Json
Write-Host "📤 Создание дайджеста..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/digests" -Method POST -ContentType "application/json" -Body $json
    Write-Host "✅ Дайджест создан! Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($response.Content)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Ошибка создания дайджеста: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. Получение списка дайджестов
Write-Host "`n📋 Получение списка дайджестов..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/digests" -Method GET
    Write-Host "✅ Список получен! Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($response.Content)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Ошибка получения списка: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Получение статистики
Write-Host "`n📊 Получение статистики..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/digests/stats/summary" -Method GET
    Write-Host "✅ Статистика получена! Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($response.Content)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Ошибка получения статистики: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. Получение конкретного дайджеста
Write-Host "`n🔍 Получение дайджеста test_digest_123..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/digests/test_digest_123" -Method GET
    Write-Host "✅ Дайджест получен! Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($response.Content)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Ошибка получения дайджеста: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎉 Тестирование завершено!" -ForegroundColor Green 