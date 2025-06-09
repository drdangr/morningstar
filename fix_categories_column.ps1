$filePath = "frontend\admin-panel\src\pages\ChannelsPage.jsx"
$content = Get-Content $filePath -Raw

Write-Host "Сжимаю колонку Категории..." -ForegroundColor Yellow

# Уменьшаем колонку Категории с 10% до 6%
$content = $content -replace 'sx=\{\{ width: "10%" \}\}.*?Категории', 'sx={{ width: "6%" }}>Категории'

# Перераспределяем освободившиеся 4% между другими колонками для лучшего баланса
# Добавляем по 1% к Каналу и Описанию (самые важные колонки)
$content = $content -replace 'sx=\{\{ width: "18%" \}\}.*?Канал', 'sx={{ width: "19%" }}>Канал'
$content = $content -replace 'sx=\{\{ width: "20%" \}\}.*?Описание', 'sx={{ width: "21%" }}>Описание'

# Теперь распределение: 19% + 8% + 21% + 12% + 8% + 6% + 12% = 86%

Set-Content $filePath $content -Encoding UTF8
Write-Host "Колонка Категории сжата до 6%! Освободившееся место распределено между Каналом и Описанием." -ForegroundColor Green 