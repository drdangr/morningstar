$filePath = "frontend/admin-panel/src/pages/ChannelsPage.jsx"
$content = Get-Content $filePath -Raw

# Исправляем ошибки синтаксиса
$content = $content -replace 'fontsize="small"', 'fontSize="small"'
$content = $content -replace 'variant="outlined">', '>'
$content = $content -replace 'size="small" variant="outlined"', 'size="small"'

# Исправляем IconButton (не поддерживает variant)
$content = $content -replace 'IconButton[^>]*variant="outlined"', 'IconButton'

# Исправляем неправильное изменение Button на IconButton в категориях
$oldCategoryButton = '<Button
                     size="small" variant="outlined"
                     onClick={() => handleManageCategories(channel)}
                     title="Управление категориями"
                   >
                     <CategoryIcon fontSize="small" />
                   </IconButton>'

$newCategoryButton = '<IconButton
                     size="small"
                     onClick={() => handleManageCategories(channel)}
                     title="Управление категориями"
                   >
                     <CategoryIcon fontSize="small" />
                   </IconButton>'

$content = $content -replace [regex]::Escape($oldCategoryButton), $newCategoryButton

# Убираем лишние variant="outlined" из Table
$content = $content -replace 'Table size="small" variant="outlined"', 'Table size="small"'

Set-Content $filePath $content -Encoding UTF8
Write-Host "Синтаксические ошибки исправлены!" -ForegroundColor Green 