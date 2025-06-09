$body = @{
    digest_id = "test_empty_digest_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    total_posts = 0
    channels_processed = 1
    original_posts = 5
    relevant_posts = 0
    avg_importance = 0.0
    avg_urgency = 0.0
    avg_significance = 0.0
    binary_relevance_applied = $true
    with_metrics = $true
    digest_data = "[]"
    processed_at = Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'
} | ConvertTo-Json

Write-Host "Тестирую пустой дайджест..."
Write-Host "Body: $body"

try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/digests" -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
    Write-Host "SUCCESS: Пустой дайджест сохранен!"
    Write-Host "Response: $($response | ConvertTo-Json -Depth 3)"
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
    Write-Host "StatusCode: $($_.Exception.Response.StatusCode)"
} 