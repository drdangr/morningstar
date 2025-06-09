$filePath = "frontend\admin-panel\src\pages\ChannelsPage.jsx"
$content = Get-Content $filePath -Raw

Write-Host "Оптимизирую ширину таблицы..." -ForegroundColor Yellow

# 1. Убираем минимальную ширину таблицы и overflowX
$content = $content -replace 'TableContainer component=\{Paper\} sx=\{\{ overflowX: ''auto'' \}\}', 'TableContainer component={Paper}'
$content = $content -replace 'Table size="small" sx=\{\{ minWidth: 800 \}\}', 'Table size="small"'

# 2. Уменьшаем ширины колонок для лучшей компактности
$content = $content -replace 'sx=\{\{ width: ''25%'', minWidth: 200 \}\}', 'sx={{ width: "20%" }}'  # Канал
$content = $content -replace 'sx=\{\{ width: ''12%'', minWidth: 120 \}\}', 'sx={{ width: "10%" }}'  # Username  
$content = $content -replace 'sx=\{\{ width: ''20%'', minWidth: 150 \}\}', 'sx={{ width: "25%" }}'  # Описание
$content = $content -replace 'sx=\{\{ width: ''12%'', minWidth: 120 \}\}', 'sx={{ width: "15%" }}'  # Telegram ID
$content = $content -replace 'sx=\{\{ width: ''8%'', minWidth: 80 \}\}', 'sx={{ width: "8%" }}'   # Статус
$content = $content -replace 'sx=\{\{ width: ''10%'', minWidth: 100 \}\}', 'sx={{ width: "10%" }}'  # Категории
$content = $content -replace 'sx=\{\{ width: ''13%'', minWidth: 100 \}\}', 'sx={{ width: "12%" }}'  # Действия

# 3. Делаем описание более компактным - обрезаем до 50 символов вместо 100
$content = $content -replace 'channel\.description\.slice\(0, 100\)', 'channel.description.slice(0, 50)'
$content = $content -replace 'channel\.description\.length > 100', 'channel.description.length > 50'

Set-Content $filePath $content -Encoding UTF8
Write-Host "Ширина таблицы оптимизирована! Горизонтальный скролл должен исчезнуть." -ForegroundColor Green 