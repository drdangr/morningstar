$filePath = "frontend\admin-panel\src\pages\ChannelsPage.jsx"
$content = Get-Content $filePath -Raw

Write-Host "Сжимаю колонку Категории до минимума..." -ForegroundColor Yellow

# Уменьшаем колонку Категории с 6% до 4%
$content = $content -replace 'sx=\{\{ width: "6%" \}\}.*?Категории', 'sx={{ width: "4%" }}>Категории'

# Перераспределяем освободившиеся 2% - добавляем по 1% к Каналу и Описанию
$content = $content -replace 'sx=\{\{ width: "19%" \}\}.*?Канал', 'sx={{ width: "20%" }}>Канал'
$content = $content -replace 'sx=\{\{ width: "21%" \}\}.*?Описание', 'sx={{ width: "22%" }}>Описание'

# Теперь распределение: 20% + 8% + 22% + 12% + 8% + 4% + 12% = 86%

Set-Content $filePath $content -Encoding UTF8
Write-Host "Колонка Категории сжата до 4%! Больше места для основного контента." -ForegroundColor Green 