$filePath = "frontend/admin-panel/src/pages/ChannelsPage.jsx"
$content = Get-Content $filePath -Raw

# Старая таблица (упрощенная версия для замены)
$oldTable = '<TableContainer component={Paper}>
        <Table>'

# Новая оптимизированная таблица
$newTable = '<TableContainer component={Paper} sx={{ overflowX: ''auto'' }}>
        <Table size="small" sx={{ minWidth: 800 }}>'

$content = $content -replace [regex]::Escape($oldTable), $newTable

# Замена заголовков колонок с фиксированными ширинами
$oldHeaders = '<TableCell>Канал</TableCell>
              <TableCell>Username</TableCell>
              <TableCell>Описание</TableCell>
              <TableCell>Telegram ID</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell>Категории</TableCell>
              <TableCell align="right">Действия</TableCell>'

$newHeaders = '<TableCell sx={{ width: ''25%'', minWidth: 200 }}>Канал</TableCell>
              <TableCell sx={{ width: ''12%'', minWidth: 120 }}>Username</TableCell>
              <TableCell sx={{ width: ''20%'', minWidth: 150 }}>Описание</TableCell>
              <TableCell sx={{ width: ''12%'', minWidth: 120 }}>Telegram ID</TableCell>
              <TableCell sx={{ width: ''8%'', minWidth: 80 }}>Статус</TableCell>
              <TableCell sx={{ width: ''10%'', minWidth: 100 }}>Категории</TableCell>
              <TableCell align="right" sx={{ width: ''13%'', minWidth: 100 }}>Действия</TableCell>'

$content = $content -replace [regex]::Escape($oldHeaders), $newHeaders

Set-Content $filePath $content -Encoding UTF8
Write-Host "Таблица оптимизирована!" -ForegroundColor Green 