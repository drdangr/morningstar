# Пошаговый debug тест
Write-Host "🔍 Debug тест - добавляем поля по одному..." -ForegroundColor Green

function Test-DigestData($data, $testName) {
    $json = $data | ConvertTo-Json
    Write-Host "`n🧪 Тест: $testName" -ForegroundColor Yellow
    Write-Host "JSON: $json" -ForegroundColor Cyan
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/digests" -Method POST -ContentType "application/json" -Body $json
        Write-Host "✅ Status: $($response.StatusCode)" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Ошибка: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "Детали: $responseBody" -ForegroundColor Yellow
        }
        return $false
    }
}

# Тест 1: только digest_id (уже работает)
$test1 = @{
    digest_id = "debug_test_1"
}
Test-DigestData $test1 "Только digest_id"

# Тест 2: добавляем integer поля
$test2 = @{
    digest_id = "debug_test_2"
    total_posts = 4
    channels_processed = 2
}
Test-DigestData $test2 "С integer полями"

# Тест 3: добавляем float поля
$test3 = @{
    digest_id = "debug_test_3"
    total_posts = 4
    channels_processed = 2
    avg_importance = [double]8.0
    avg_urgency = [double]6.75
}
Test-DigestData $test3 "С float полями"

# Тест 4: добавляем boolean поля
$test4 = @{
    digest_id = "debug_test_4"
    total_posts = 4
    channels_processed = 2
    avg_importance = [double]8.0
    binary_relevance_applied = $true
    with_metrics = $true
}
Test-DigestData $test4 "С boolean полями"

# Тест 5: добавляем дату (подозрительное поле!)
$test5 = @{
    digest_id = "debug_test_5"
    total_posts = 4
    binary_relevance_applied = $true
    processed_at = "2025-12-08T10:00:00Z"
}
Test-DigestData $test5 "С датой (ISO формат)"

Write-Host "`n🎯 Debug завершен!" -ForegroundColor Green 