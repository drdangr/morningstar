$filePath = "frontend\admin-panel\src\pages\ChannelsPage.jsx"
$content = Get-Content $filePath -Raw

Write-Host "Исправляю JSX ошибки..." -ForegroundColor Yellow

# 1. Исправляем Button/IconButton несоответствие (строка 558)
$content = $content -replace '<Button\s+size="small"\s+variant="outlined"\s+onClick=\{\(\) => handleManageCategories\(channel\)\}[^>]*>\s*<CategoryIcon[^>]*>\s*</IconButton>', '<IconButton size="small" onClick={() => handleManageCategories(channel)} title="Управление категориями"><CategoryIcon fontSize="small" /></IconButton>'

# 2. Убираем variant="outlined" из IconButton (они его не поддерживают)
$content = $content -replace 'IconButton\s+size="small"\s+variant="outlined"', 'IconButton size="small"'

# 3. Убираем variant="outlined" из Chip (строка 547) 
$content = $content -replace 'size="small"\s+variant="outlined"\s+icon=', 'size="small" icon='

# 4. Убираем variant="outlined" из Button в Alert action
$content = $content -replace 'Button\s+color="inherit"\s+size="small"\s+variant="outlined"\s+onClick=\{applyValidationResult\}', 'Button color="inherit" size="small" onClick={applyValidationResult}'

Set-Content $filePath $content -Encoding UTF8
Write-Host "Все JSX ошибки исправлены!" -ForegroundColor Green 