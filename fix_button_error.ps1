$filePath = "frontend/admin-panel/src/pages/ChannelsPage.jsx"
$content = Get-Content $filePath -Raw

# Исправляем неправильную кнопку "Использовать"
$oldButton = '<Button color="inherit" size="small" onClick={applyValidationResult}>
                          Использовать
                        </Button>'

$newButton = '<Button color="inherit" size="small" onClick={applyValidationResult}>
                          Использовать
                        </Button>'

# Проверяем и исправляем структуру Alert
$content = $content -replace 'variant="outlined" onClick={applyValidationResult}', 'onClick={applyValidationResult}'

Set-Content $filePath $content -Encoding UTF8
Write-Host "Button ошибка исправлена!" -ForegroundColor Green 