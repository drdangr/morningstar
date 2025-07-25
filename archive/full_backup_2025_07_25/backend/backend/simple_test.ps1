# Простой тест с минимальными данными
Write-Host "🔍 Простой тест Digest API..." -ForegroundColor Green

# Минимальные данные
$digestData = @{
    digest_id = "simple_test_456"
}

$json = $digestData | ConvertTo-Json
Write-Host "JSON: $json" -ForegroundColor Cyan

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/digests" -Method POST -ContentType "application/json" -Body $json
    Write-Host "✅ Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($response.Content)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Ошибка: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Детали ошибки: $responseBody" -ForegroundColor Yellow
    }
} 