$filePath = "frontend/admin-panel/src/pages/ChannelsPage.jsx"
$content = Get-Content $filePath -Raw

# Компактные иконки и текст
$content = $content -replace 'width: 32, height: 32', 'width: 28, height: 28'
$content = $content -replace 'mr: 2', 'mr: 1.5'
$content = $content -replace '<TelegramIcon />', '<TelegramIcon fontSize="small" />'

# Компактный статус
$content = $content -replace "'Активен' : 'Неактивен'", "'Вкл' : 'Выкл'"
$content = $content -replace 'size="small"', 'size="small" variant="outlined"'

# Hover эффект
$content = $content -replace '<TableRow key={channel.id}>', '<TableRow key={channel.id} hover>'

# Компактные иконки действий  
$content = $content -replace '<EditIcon />', '<EditIcon fontSize="small" />'
$content = $content -replace '<DeleteIcon />', '<DeleteIcon fontSize="small" />'
$content = $content -replace '<CategoryIcon />', '<CategoryIcon fontSize="small" />'

# Улучшение колонки действий
$oldActions = 'startIcon={<CategoryIcon fontSize="small" />}
                    onClick={() => handleManageCategories(channel)}
                    variant="outlined"
                  >
                    Категории
                  </Button>'

$newActions = 'onClick={() => handleManageCategories(channel)}
                    title="Управление категориями"
                  >
                    <CategoryIcon fontSize="small" />
                  </IconButton>'

$content = $content -replace [regex]::Escape($oldActions), $newActions

Set-Content $filePath $content -Encoding UTF8
Write-Host "Таблица сделана более компактной!" -ForegroundColor Green 