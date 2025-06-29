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
  Warning as WarningIcon,
  Storage as StorageIcon
} from '@mui/icons-material';

// Определяем API URL динамически
const API_BASE_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000' 
  : 'http://localhost:8000';

function RawPostsTab({ stats, onStatsUpdate }) {
  // Состояние для данных
  const [posts, setPosts] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [dataSize, setDataSize] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Состояние для диалогов очистки
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

  // Загрузка RAW постов (без AI данных)
  const loadRawPosts = async () => {
    setLoading(true);
    setError('');

    try {
      console.log('🔄 Загружаем RAW посты...');
      
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

      // Используем endpoint /api/posts/cache (без AI данных)
      const [postsResponse, countResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/api/posts/cache?${params}`),
        fetch(`${API_BASE_URL}/api/posts/cache/count?${params}`)
      ]);

      if (!postsResponse.ok) {
        throw new Error(`HTTP ${postsResponse.status}: ${postsResponse.statusText}`);
      }

      const postsData = await postsResponse.json();
      const countData = await countResponse.json();

      console.log('✅ RAW посты загружены:', postsData.length);
      setPosts(postsData);
      setTotalCount(countData.total_count);
      
      // Загружаем размер данных для текущих фильтров
      loadDataSize();
    } catch (err) {
      console.error('❌ Ошибка загрузки RAW постов:', err);
      setError('Ошибка загрузки постов: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Загрузка данных при изменении фильтров
  useEffect(() => {
    loadRawPosts();
  }, [page, rowsPerPage, search, channelFilter, statusFilter, dateFrom, dateTo, sortBy, sortOrder]);

  // Обработчики событий
  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  const handleRowsPerPageChange = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleClearFilters = () => {
    setSearch('');
    setChannelFilter('');
    setStatusFilter('');
    setDateFrom(null);
    setDateTo(null);
    setPage(0);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU');
  };

  const formatViews = (views) => {
    if (views >= 1000000) return `${(views / 1000000).toFixed(1)}M`;
    if (views >= 1000) return `${(views / 1000).toFixed(1)}K`;
    return views?.toString() || '0';
  };

  const getChannelInfo = (telegramId) => {
    if (!stats?.channels) return { title: `ID: ${telegramId}`, username: '' };
    
    const channel = stats.channels.find(ch => ch.telegram_id === telegramId);
    if (!channel) return { title: `ID: ${telegramId}`, username: '' };
    
    return {
      title: channel.title || channel.channel_name || `ID: ${telegramId}`,
      username: channel.username || ''
    };
  };

  const truncateText = (text, maxLength = 100) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  const cleanMarkdownText = (text) => {
    if (!text) return '';
    
    return text
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/__(.*?)__/g, '$1')
      .replace(/_(.*?)_/g, '$1')
      .replace(/`(.*?)`/g, '$1')
      .replace(/\[(.*?)\]\(.*?\)/g, '$1')
      .replace(/#{1,6}\s/g, '')
      .replace(/>\s/g, '')
      .replace(/\n+/g, ' ')
      .trim();
  };

  const handleCleanupOrphans = async () => {
    setClearingOrphans(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/posts/orphans?confirm=true`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        const result = await response.json();
        setOrphanSuccess(`Удалено ${result.deleted_count} постов-сирот`);
        loadRawPosts();
        onStatsUpdate();
      } else {
        throw new Error('Ошибка при удалении постов-сирот');
      }
    } catch (err) {
      setError('Ошибка очистки: ' + err.message);
    } finally {
      setClearingOrphans(false);
      setOrphanConfirmDialog(false);
    }
  };

  return (
    <Box>
      {/* Заголовок таба */}
      <Box display="flex" alignItems="center" gap={2} sx={{ mb: 3 }}>
        <StorageIcon color="primary" />
        <Typography variant="h5">
          RAW POSTS - Данные Userbot
        </Typography>
        <Chip 
          label={`${totalCount.toLocaleString()} постов`} 
          color="primary" 
          variant="outlined" 
        />
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Чистые данные от Userbot без AI обработки. Быстрая загрузка, фильтрация по каналам, датам и содержимому.
      </Typography>

      {/* Статистика RAW данных */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Отображено постов
              </Typography>
              <Typography variant="h6">
                {posts.length} из {totalCount.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Размер данных
              </Typography>
              <Typography variant="h6">
                {dataSize ? `${dataSize.toFixed(1)} MB` : 'Загрузка...'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Активные фильтры
              </Typography>
              <Typography variant="h6">
                {[search, channelFilter, statusFilter, dateFrom, dateTo].filter(Boolean).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Страница
              </Typography>
              <Typography variant="h6">
                {page + 1} из {Math.ceil(totalCount / rowsPerPage)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Ошибки */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Фильтры */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Фильтры и поиск
        </Typography>
        
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="Поиск по содержимому"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Канал</InputLabel>
              <Select
                value={channelFilter}
                onChange={(e) => setChannelFilter(e.target.value)}
                label="Канал"
              >
                <MenuItem value="">Все каналы</MenuItem>
                {stats?.channels?.map((channel) => (
                  <MenuItem key={channel.telegram_id} value={channel.telegram_id}>
                    {channel.title || channel.channel_name} ({channel.posts_count})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Статус</InputLabel>
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                label="Статус"
              >
                <MenuItem value="">Все статусы</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="processing">Processing</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Box display="flex" gap={1}>
              <Button
                variant="outlined"
                onClick={handleClearFilters}
                startIcon={<ClearIcon />}
              >
                Очистить
              </Button>
              <Button
                variant="contained"
                onClick={loadRawPosts}
                startIcon={<RefreshIcon />}
                disabled={loading}
              >
                Обновить
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Таблица постов */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Канал</TableCell>
              <TableCell>Содержимое</TableCell>
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
                  <Typography color="text.secondary">
                    Нет данных для отображения
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              posts.map((post) => {
                const channelInfo = getChannelInfo(post.channel_telegram_id);
                
                return (
                  <TableRow key={post.id} hover>
                    <TableCell>{post.id}</TableCell>
                    
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="bold">
                          {channelInfo.title}
                        </Typography>
                        {channelInfo.username && (
                          <Typography variant="caption" color="text.secondary">
                            @{channelInfo.username}
                          </Typography>
                        )}
                        <Typography variant="caption" display="block" color="text.secondary">
                          ID: {post.channel_telegram_id}
                        </Typography>
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Box sx={{ maxWidth: 300 }}>
                        {post.title && (
                          <Typography variant="body2" fontWeight="bold" gutterBottom>
                            {truncateText(post.title, 50)}
                          </Typography>
                        )}
                        <Typography variant="body2" color="text.secondary">
                          {truncateText(cleanMarkdownText(post.content), 100)}
                        </Typography>
                        {post.media_urls && post.media_urls.length > 0 && (
                          <Chip 
                            label={`📎 ${post.media_urls.length} медиа`} 
                            size="small" 
                            sx={{ mt: 1 }} 
                          />
                        )}
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2">
                        {formatViews(post.views)}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2">
                        {formatDate(post.post_date)}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2">
                        {formatDate(post.collected_at)}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Chip 
                        label={post.processing_status || 'pending'} 
                        size="small"
                        color={
                          post.processing_status === 'completed' ? 'success' :
                          post.processing_status === 'processing' ? 'warning' :
                          post.processing_status === 'failed' ? 'error' :
                          'default'
                        }
                      />
                    </TableCell>
                    
                    <TableCell>
                      <Box display="flex" gap={1}>
                        <Tooltip title="Просмотр в Telegram">
                          <IconButton
                            size="small"
                            onClick={() => window.open(`https://t.me/c/${Math.abs(post.channel_telegram_id)}/1${post.telegram_message_id}`, '_blank')}
                          >
                            <LinkIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Детали поста">
                          <IconButton size="small">
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Пагинация */}
      <TablePagination
        component="div"
        count={totalCount}
        page={page}
        onPageChange={handlePageChange}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={handleRowsPerPageChange}
        rowsPerPageOptions={[10, 25, 50, 100]}
        labelRowsPerPage="Строк на странице:"
        labelDisplayedRows={({ from, to, count }) => 
          `${from}-${to} из ${count !== -1 ? count : `более ${to}`}`
        }
      />

      {/* Диалог подтверждения очистки orphan постов */}
      <Dialog open={orphanConfirmDialog} onClose={() => setOrphanConfirmDialog(false)}>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <WarningIcon color="warning" />
            Очистка постов-сирот
          </Box>
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Вы уверены, что хотите удалить все посты из каналов, которые не используются активными ботами?
            Это действие нельзя отменить.
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
            startIcon={clearingOrphans ? <CircularProgress size={20} /> : <DeleteIcon />}
          >
            {clearingOrphans ? 'Удаление...' : 'Удалить'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar для успешных операций */}
      <Snackbar
        open={!!orphanSuccess}
        autoHideDuration={6000}
        onClose={() => setOrphanSuccess('')}
        message={orphanSuccess}
      />
    </Box>
  );
}

export default RawPostsTab; 