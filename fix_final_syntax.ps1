$filePath = "frontend\admin-panel\src\pages\ChannelsPage.jsx"
$content = Get-Content $filePath -Raw

# Исправляем неправильное несоответствие тегов Button/IconButton
$content = $content -replace '<Button\s+size="small"\s+onClick=\{\(\) => handleManageCategories\(channel\)\}\s+title="Управление категориями"\s+>', '<IconButton size="small" onClick={() => handleManageCategories(channel)} title="Управление категориями">'

Set-Content $filePath $content -Encoding UTF8
Write-Host "Финальная ошибка синтаксиса исправлена!" -ForegroundColor Green 