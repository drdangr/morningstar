# Тест проблемного поля digest_data
Write-Host "🔍 Тестируем поле digest_data..." -ForegroundColor Green

function Test-DigestData($data, $testName) {
    $json = $data | ConvertTo-Json -Depth 10
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

# Тест 1: С простой строкой в digest_data
$test1 = @{
    digest_id = "digest_data_test_1"
    digest_data = "простая строка"
}
Test-DigestData $test1 "С простой строкой в digest_data"

# Тест 2: С JSON строкой в digest_data (ПОДОЗРИТЕЛЬНО!)
$test2 = @{
    digest_id = "digest_data_test_2"
    digest_data = '{"channels":[{"title":"Breaking Mash","username":"@breakingmash","posts_count":2}]}'
}
Test-DigestData $test2 "С JSON строкой в digest_data"

# Тест 3: Полные данные как в исходном тесте
$test3 = @{
    digest_id = "digest_data_test_3"
    total_posts = 4
    channels_processed = 2
    original_posts = 10
    relevant_posts = 4
    avg_importance = [double]8.0
    avg_urgency = [double]6.75
    avg_significance = [double]7.5
    binary_relevance_applied = $true
    with_metrics = $true
    digest_data = '{"channels":[{"title":"Breaking Mash","username":"@breakingmash","posts_count":2}]}'
    processed_at = "2025-12-08T10:00:00Z"
}
Test-DigestData $test3 "Полные данные (исходный тест)"

Write-Host "`n🎯 Тест digest_data завершен!" -ForegroundColor Green 