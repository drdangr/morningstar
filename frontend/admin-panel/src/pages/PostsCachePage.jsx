import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Box,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Button,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Snackbar
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Clear as ClearIcon,
  Visibility as ViewIcon,
  Link as LinkIcon,
  Schedule as ScheduleIcon,
  Delete as DeleteIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
// Временно закомментируем DateTimePicker до установки правильных зависимостей
// import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
// import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
// import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
// import { ru } from 'date-fns/locale';

const API_BASE_URL = 'http://localhost:8000';

function PostsCachePage() {
  // Состояние для данных
  const [posts, setPosts] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [stats, setStats] = useState(null);
  const [dataSize, setDataSize] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Состояние для диалогов очистки базы
  const [firstWarningDialog, setFirstWarningDialog] = useState(false);
  const [finalConfirmDialog, setFinalConfirmDialog] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [clearSuccess, setClearSuccess] = useState('');

  // Состояние для очистки orphan постов
  const [orphanConfirmDialog, setOrphanConfirmDialog] = useState(false);
  const [clearingOrphans, setClearingOrphans] = useState(false);
  const [orphanSuccess, setOrphanSuccess] = useState('');

  // Состояние для фильтров
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [search, setSearch] = useState('');
  const [channelFilter, setChannelFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [dateFrom, setDateFrom] = useState(null);
  const [dateTo, setDateTo] = useState(null);
  const [sortBy, setSortBy] = useState('collected_at');
  const [sortOrder, setSortOrder] = useState('desc');

  // Загрузка статистики
  const loadStats = async () => {
    try {
      console.log('🔄 Загружаем статистику постов...');
      const response = await fetch(`${API_BASE_URL}/api/posts/stats`);
      console.log('📊 Ответ API статистики:', response.status, response.statusText);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ Данные статистики получены:', data);
      console.log('📺 Каналы в статистике:', data.channels?.length || 0);
      
      if (data.channels) {
        data.channels.forEach((channel, index) => {
          console.log(`   Канал ${index + 1}: ${channel.telegram_id} - ${channel.title}`);
        });
      }
      
      setStats(data);
      console.log('💾 Статистика сохранена в состояние');
    } catch (err) {
      console.error('❌ Ошибка загрузки статистики:', err);
      setError('Ошибка загрузки статистики: ' + err.message);
    }
  };

  // Загрузка размера данных
  const loadDataSize = async () => {
    try {
      const params = new URLSearchParams();
      if (channelFilter) params.append('channel_telegram_id', channelFilter);
      
      const response = await fetch(`${API_BASE_URL}/api/posts/cache/size?${params}`);
      const data = await response.json();
      setDataSize(data.size_mb);
    } catch (err) {
      console.error('Ошибка загрузки размера данных:', err);
    }
  };

  // Загрузка постов с фильтрами
  const loadPosts = async () => {
    setLoading(true);
    setError('');

    try {
      // Параметры запроса
      const params = new URLSearchParams({
        skip: page * rowsPerPage,
        limit: rowsPerPage,
        sort_by: sortBy,
        sort_order: sortOrder
      });

      if (search) params.append('search', search);
      if (channelFilter) params.append('channel_telegram_id', channelFilter);
      if (statusFilter) params.append('processing_status', statusFilter);
      if (dateFrom) params.append('date_from', dateFrom.toISOString());
      if (dateTo) params.append('date_to', dateTo.toISOString());

      // Загружаем посты и количество параллельно
      const [postsResponse, countResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/api/posts/cache?${params}`),
        fetch(`${API_BASE_URL}/api/posts/cache/count?${params}`)
      ]);

      const postsData = await postsResponse.json();
      const countData = await countResponse.json();

      setPosts(postsData);
      setTotalCount(countData.total_count);
      
      // Загружаем размер данных для текущих фильтров
      loadDataSize();
    } catch (err) {
      setError('Ошибка загрузки постов: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Загрузка данных при изменении фильтров
  useEffect(() => {
    loadPosts();
  }, [page, rowsPerPage, search, channelFilter, statusFilter, dateFrom, dateTo, sortBy, sortOrder]);

  // Загрузка статистики при монтировании
  useEffect(() => {
    console.log('🚀 Компонент PostsCachePage монтируется, загружаем статистику...');
    loadStats();
  }, []);

  // Сброс фильтров
  const handleClearFilters = () => {
    setSearch('');
    setChannelFilter('');
    setStatusFilter('');
    setDateFrom(null);
    setDateTo(null);
    setPage(0);
  };

  // Форматирование даты
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU');
  };

  // Форматирование числа просмотров
  const formatViews = (views) => {
    if (views >= 1000000) return `${(views / 1000000).toFixed(1)}M`;
    if (views >= 1000) return `${(views / 1000).toFixed(1)}K`;
    return views.toString();
  };

  // Получение информации о канале из статистики
  const getChannelInfo = (telegramId) => {
    console.log(`🔍 Ищем информацию о канале ${telegramId}`);
    console.log('📊 Состояние stats:', stats ? 'загружено' : 'null');
    
    if (!stats) {
      console.log(`❌ Stats не загружены, возвращаем fallback для ${telegramId}`);
      return { title: `Channel ${telegramId}`, username: null };
    }
    
    console.log(`📺 Доступные каналы в stats: ${stats.channels?.length || 0}`);
    if (stats.channels) {
      stats.channels.forEach(ch => {
        console.log(`   - ${ch.telegram_id}: ${ch.title}`);
      });
    }
    
    const channel = stats.channels?.find(ch => ch.telegram_id === telegramId);
    
    if (channel) {
      console.log(`✅ Канал ${telegramId} найден: ${channel.title}`);
      return channel;
    } else {
      console.log(`❌ Канал ${telegramId} НЕ найден в stats, возвращаем fallback`);
      return { title: `Channel ${telegramId}`, username: null };
    }
  };

  // Обрезка текста
  const truncateText = (text, maxLength = 100) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  // Обработка очистки orphan постов
  const handleCleanupOrphans = async () => {
    try {
      setClearingOrphans(true);
      const response = await fetch(`${API_BASE_URL}/api/posts/orphans?confirm=true`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Ошибка очистки orphan постов');
      }

      const result = await response.json();
      setOrphanSuccess(result.message);  
      setOrphanConfirmDialog(false);
      
      // Перезагружаем данные
      loadPosts();
      loadStats();
    } catch (err) {
      setError('Ошибка очистки orphan постов: ' + err.message);
      setOrphanConfirmDialog(false);
    } finally {
      setClearingOrphans(false);
    }
  };

  // Обработка очистки базы данных
  const handleClearDatabase = async () => {
    try {
      setClearing(true);
      const response = await fetch(`${API_BASE_URL}/api/database/clear?confirm=true`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Ошибка очистки базы данных');
      }

      const result = await response.json();
      setClearSuccess(`База очищена успешно! Удалено: ${result.deleted_posts} постов, ${result.deleted_digests} дайджестов`);
      setFinalConfirmDialog(false);
      
      // Перезагружаем данные
      loadPosts();
      loadStats();
    } catch (err) {
      setError('Ошибка очистки базы: ' + err.message);
      setFinalConfirmDialog(false);
    } finally {
      setClearing(false);
    }
  };

  const handleFirstWarning = () => {
    setFirstWarningDialog(false);
    setFinalConfirmDialog(true);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Posts Cache Monitor
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            color="warning"
            startIcon={<WarningIcon />}
            onClick={() => setOrphanConfirmDialog(true)}
            size="large"
            disabled={clearingOrphans}
          >
            {clearingOrphans ? 'Очистка...' : 'Очистить Orphan Посты'}
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={() => setFirstWarningDialog(true)}
            size="large"
            sx={{ minWidth: 200 }}
          >
            Очистить База Данных
          </Button>
        </Box>
      </Box>

        {/* Статистика */}
        {stats && (
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Всего постов
                  </Typography>
                  <Typography variant="h5">
                    {stats.total_posts}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Каналов
                  </Typography>
                  <Typography variant="h5">
                    {stats.channels.length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Pending
                  </Typography>
                  <Typography variant="h5">
                    {stats.processing_status.find(s => s.status === 'pending')?.count || 0}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    {channelFilter ? 'Размер отфильтрованных данных' : 'Размер данных'}
                  </Typography>
                  <Typography variant="h5">
                    {dataSize.toFixed(2)} MB
                  </Typography>
                  {channelFilter && (
                    <Typography variant="caption" color="textSecondary">
                      Канал: {getChannelInfo(parseInt(channelFilter)).title}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Фильтры */}
        <Paper sx={{ p: 2, mb: 2 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                placeholder="Поиск по содержимому..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon color="action" />,
                }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Канал</InputLabel>
                <Select
                  value={channelFilter}
                  label="Канал"
                  onChange={(e) => setChannelFilter(e.target.value)}
                >
                  <MenuItem value="">Все каналы</MenuItem>
                  {stats?.channels.map((channel) => (
                    <MenuItem key={channel.telegram_id} value={channel.telegram_id}>
                      {channel.title}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Статус</InputLabel>
                <Select
                  value={statusFilter}
                  label="Статус"
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <MenuItem value="">Все статусы</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="processing">Processing</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
                         <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="Дата от"
                type="datetime-local"
                value={dateFrom ? dateFrom.toISOString().slice(0, 16) : ''}
                onChange={(e) => setDateFrom(e.target.value ? new Date(e.target.value) : null)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="Дата до"
                type="datetime-local"
                value={dateTo ? dateTo.toISOString().slice(0, 16) : ''}
                onChange={(e) => setDateTo(e.target.value ? new Date(e.target.value) : null)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={1}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Tooltip title="Обновить">
                  <IconButton onClick={loadPosts}>
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Сбросить фильтры">
                  <IconButton onClick={handleClearFilters}>
                    <ClearIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Grid>
          </Grid>
        </Paper>

        {/* Ошибки */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Таблица */}
        <Paper>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Канал</TableCell>
                  <TableCell>Содержание</TableCell>
                  <TableCell>Просмотры</TableCell>
                  <TableCell>Дата поста</TableCell>
                  <TableCell>Собрано</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell>Действия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      <CircularProgress />
                    </TableCell>
                  </TableRow>
                ) : posts.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      Постов не найдено
                    </TableCell>
                  </TableRow>
                ) : (
                  posts.map((post) => {
                    const channelInfo = getChannelInfo(post.channel_telegram_id);
                    return (
                      <TableRow key={post.id}>
                        <TableCell>{post.telegram_message_id}</TableCell>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" fontWeight="bold">
                              {channelInfo.title}
                            </Typography>
                            {channelInfo.username && (
                              <Typography variant="caption" color="textSecondary">
                                @{channelInfo.username}
                              </Typography>
                            )}
                          </Box>
                        </TableCell>
                        <TableCell sx={{ maxWidth: 300 }}>
                          {post.title && (
                            <Typography variant="body2" fontWeight="bold" gutterBottom>
                              {truncateText(post.title, 50)}
                            </Typography>
                          )}
                          <Typography variant="body2">
                            {truncateText(post.content, 100)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <ViewIcon fontSize="small" color="action" />
                            {formatViews(post.views)}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <ScheduleIcon fontSize="small" color="action" />
                            {formatDate(post.post_date)}
                          </Box>
                        </TableCell>
                        <TableCell>
                          {formatDate(post.collected_at)}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={post.processing_status}
                            color={
                              post.processing_status === 'completed' ? 'success' :
                              post.processing_status === 'processing' ? 'warning' :
                              post.processing_status === 'failed' ? 'error' : 'default'
                            }
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {post.media_urls && post.media_urls.length > 0 && (
                            <Tooltip title={`${post.media_urls.length} медиафайлов`}>
                              <IconButton size="small">
                                <LinkIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            rowsPerPageOptions={[10, 25, 50, 100]}
            component="div"
            count={totalCount}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
            labelRowsPerPage="Строк на странице:"
            labelDisplayedRows={({ from, to, count }) => `${from}-${to} из ${count}`}
          />
        </Paper>

        {/* Первое предупреждение */}
        <Dialog
          open={firstWarningDialog}
          onClose={() => setFirstWarningDialog(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>
            <Box display="flex" alignItems="center" gap={2}>
              <WarningIcon color="warning" />
              <Typography variant="h6" color="warning.main">
                Предупреждение
              </Typography>
            </Box>
          </DialogTitle>
          <DialogContent>
            <DialogContentText sx={{ fontSize: '1.1rem' }}>
              ⚠️ Вы собираетесь выполнить критическое действие - <strong>полную очистку базы данных</strong>.
            </DialogContentText>
            <DialogContentText sx={{ mt: 2 }}>
              Это действие удалит:
            </DialogContentText>
            <Box component="ul" sx={{ mt: 1, mb: 2 }}>
              <li>Все посты из кеша ({stats?.total_posts || 0} постов)</li>
              <li>Все созданные дайджесты ({stats?.processing_status?.find(s => s.status === 'pending')?.count || 0} pending)</li>
              <li>Освободит {dataSize.toFixed(2)} MB дискового пространства</li>
            </Box>
            <DialogContentText color="error.main" sx={{ fontWeight: 'bold' }}>
              Данные нельзя будет восстановить!
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setFirstWarningDialog(false)}>
              Отмена
            </Button>
            <Button
              onClick={handleFirstWarning}
              color="warning"
              variant="contained"
            >
              Я понимаю, продолжить
            </Button>
          </DialogActions>
        </Dialog>

        {/* Финальное подтверждение */}
        <Dialog
          open={finalConfirmDialog}
          onClose={() => setFinalConfirmDialog(false)}
          maxWidth="xs"
          fullWidth
        >
          <DialogTitle>
            <Box display="flex" alignItems="center" gap={2}>
              <WarningIcon color="error" />
              <Typography variant="h6" color="error">
                Финальное подтверждение
              </Typography>
            </Box>
          </DialogTitle>
          <DialogContent>
            <DialogContentText sx={{ fontSize: '1.1rem', textAlign: 'center' }}>
              🚨 <strong>ДЕЙСТВИТЕЛЬНО УДАЛИТЬ ВСЕ ДАННЫЕ?</strong>
            </DialogContentText>
            <DialogContentText sx={{ mt: 2, textAlign: 'center' }}>
              Это последнее предупреждение.
              <br />
              Нажмите "Удалить всё" для окончательного удаления.
            </DialogContentText>
          </DialogContent>
          <DialogActions sx={{ justifyContent: 'center', gap: 2 }}>
            <Button
              onClick={() => setFinalConfirmDialog(false)}
              variant="outlined"
              size="large"
            >
              Отмена
            </Button>
            <Button
              onClick={handleClearDatabase}
              color="error"
              variant="contained"
              size="large"
              disabled={clearing}
              startIcon={clearing ? <CircularProgress size={20} /> : <DeleteIcon />}
            >
              {clearing ? 'Удаление...' : 'Удалить всё'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Уведомление об успешной очистке */}
        <Snackbar
          open={!!clearSuccess}
          autoHideDuration={6000}
          onClose={() => setClearSuccess('')}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert severity="success" onClose={() => setClearSuccess('')}>
            {clearSuccess}
          </Alert>
        </Snackbar>

        {/* Диалог подтверждения orphan cleanup */}
        <Dialog
          open={orphanConfirmDialog}
          onClose={() => setOrphanConfirmDialog(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>
            <Box display="flex" alignItems="center" gap={2}>
              <WarningIcon color="warning" />
              <Typography variant="h6" color="warning.main">
                Очистка Orphan Постов
              </Typography>
            </Box>
          </DialogTitle>
          <DialogContent>
            <DialogContentText sx={{ fontSize: '1.1rem' }}>
              🧹 Эта операция удалит посты от каналов, которые больше не активны в системе.
            </DialogContentText>
            <DialogContentText sx={{ mt: 2 }}>
              Orphan посты - это посты в posts_cache от каналов, которые были удалены из таблицы channels.
            </DialogContentText>
            <DialogContentText sx={{ mt: 2 }}>
              Текущая ситуация:
            </DialogContentText>
            <Box component="ul" sx={{ mt: 1, mb: 2 }}>
              <li>Активных каналов в системе: {stats?.channels?.filter(c => stats.channels.find(ch => ch.telegram_id === c.telegram_id))?.length || 0}</li>
              <li>Каналов в posts_cache: {stats?.channels?.length || 0}</li>
              <li>Возможно orphan каналов: {stats ? stats.channels.length - 2 : 0}</li>
            </Box>
            <DialogContentText color="info.main" sx={{ fontWeight: 'bold' }}>
              Эта операция безопасна и рекомендуется для очистки мусорных данных.
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOrphanConfirmDialog(false)}>
              Отмена
            </Button>
            <Button
              onClick={handleCleanupOrphans}
              color="warning"
              variant="contained"
              disabled={clearingOrphans}
              startIcon={clearingOrphans ? <CircularProgress size={20} /> : <WarningIcon />}
            >
              {clearingOrphans ? 'Очистка...' : 'Очистить Orphan Посты'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Уведомление об успешной очистке orphan */}
        <Snackbar
          open={!!orphanSuccess}
          autoHideDuration={6000}
          onClose={() => setOrphanSuccess('')}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert severity="success" onClose={() => setOrphanSuccess('')}>
            {orphanSuccess}
          </Alert>
        </Snackbar>
      </Box>
  );
}

export default PostsCachePage; 