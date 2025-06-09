$filePath = "frontend\admin-panel\src\pages\ChannelsPage.jsx"
$content = Get-Content $filePath -Raw

Write-Host "Делаю таблицу максимально компактной..." -ForegroundColor Yellow

# 1. Еще больше уменьшаем ширины колонок
$content = $content -replace 'sx=\{\{ width: "20%" \}\}', 'sx={{ width: "18%" }}'  # Канал
$content = $content -replace 'sx=\{\{ width: "10%" \}\}', 'sx={{ width: "8%" }}'   # Username  
$content = $content -replace 'sx=\{\{ width: "25%" \}\}', 'sx={{ width: "20%" }}'  # Описание
$content = $content -replace 'sx=\{\{ width: "15%" \}\}', 'sx={{ width: "12%" }}'  # Telegram ID
# Статус, Категории, Действия остаются: 8% + 10% + 12% = 30%
# Итого: 18% + 8% + 20% + 12% + 8% + 10% + 12% = 88% (оставляем запас)

# 2. Делаем названия каналов короче - обрезаем до 15 символов
$content = $content -replace 'channel\.title', 'channel.title.length > 15 ? channel.title.slice(0, 15) + "..." : channel.title'

# 3. Делаем описание еще короче - до 30 символов
$content = $content -replace 'channel\.description\.slice\(0, 50\)', 'channel.description.slice(0, 30)'
$content = $content -replace 'channel\.description\.length > 50', 'channel.description.length > 30'

# 4. Уменьшаем размер аватаров до 24px
$content = $content -replace 'Avatar sx=\{\{ width: 28, height: 28, mr: 1\.5 \}\}', 'Avatar sx={{ width: 24, height: 24, mr: 1 }}'

# 5. Убираем word-wrap и делаем текст в одну строку
$content = $content -replace 'Typography variant="body2" fontWeight="medium"', 'Typography variant="body2" fontWeight="medium" sx={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}'

Set-Content $filePath $content -Encoding UTF8
Write-Host "Таблица максимально сжата! Скролл должен исчезнуть." -ForegroundColor Green 