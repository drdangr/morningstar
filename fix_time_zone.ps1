$file = "frontend/admin-panel/src/pages/DashboardPage.jsx"
$content = Get-Content $file -Raw

$old = "const date = new Date(dateString);"
$new = "// Добавляем 'Z' если нет временной зоны, чтобы парсить как UTC
      const utcDateString = dateString.includes('Z') || dateString.includes('+') ? dateString : dateString + 'Z';
      const date = new Date(utcDateString);"

$newContent = $content -replace [regex]::Escape($old), $new
$newContent | Set-Content $file

Write-Host "✅ Исправлено обработка UTC времени в дашборде" 