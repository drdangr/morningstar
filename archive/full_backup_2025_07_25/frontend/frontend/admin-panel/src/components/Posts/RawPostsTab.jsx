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
  Snackbar,
  Collapse,
  Checkbox
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
  Storage as StorageIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon
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

  // Состояние для bulk delete функциональности
  const [selectedPosts, setSelectedPosts] = useState(new Set());
  const [bulkDeleteConfirmDialog, setBulkDeleteConfirmDialog] = useState(false);
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [bulkDeleteSuccess, setBulkDeleteSuccess] = useState('');

  // Состояние для фильтров
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [search, setSearch] = useState('');
  const [channelFilter, setChannelFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [dateFrom, setDateFrom] = useState(null);
  const [dateTo, setDateTo] = useState(null);
  const [sortBy, setSortBy] = useState('post_date');
  const [sortOrder, setSortOrder] = useState('desc');

  // Состояние для разворачивания постов
  const [expandedPosts, setExpandedPosts] = useState({});

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

  // Очистка выбранных постов при смене страницы или фильтров
  useEffect(() => {
    clearSelectedPosts();
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

  // Функции для работы с checkbox bulk delete
  const handleSelectAllPosts = (event) => {
    if (event.target.checked) {
      // Выбираем все посты на текущей странице
      const currentPagePostIds = new Set(posts.map(post => post.id));
      setSelectedPosts(currentPagePostIds);
    } else {
      // Снимаем выбор со всех постов
      setSelectedPosts(new Set());
    }
  };

  const handleSelectPost = (postId) => {
    const newSelected = new Set(selectedPosts);
    if (newSelected.has(postId)) {
      newSelected.delete(postId);
    } else {
      newSelected.add(postId);
    }
    setSelectedPosts(newSelected);
  };

  const handleBulkDelete = async () => {
    if (selectedPosts.size === 0) {
      setError('Не выбран ни один пост для удаления');
      return;
    }

    setBulkDeleting(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/posts/cache/bulk-delete`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          post_ids: Array.from(selectedPosts)
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка удаления постов');
      }

      const result = await response.json();
      
      // Успешное удаление
      setBulkDeleteSuccess(`Успешно удалено ${result.deleted_count} постов`);
      setSelectedPosts(new Set());
      setBulkDeleteConfirmDialog(false);
      
      // Обновляем данные
      loadRawPosts();
      if (onStatsUpdate) onStatsUpdate();
      
    } catch (err) {
      console.error('❌ Ошибка bulk delete:', err);
      setError('Ошибка удаления постов: ' + err.message);
    } finally {
      setBulkDeleting(false);
    }
  };

  const clearSelectedPosts = () => {
    setSelectedPosts(new Set());
  };

  // Проверяем, выбраны ли все посты на текущей странице
  const isAllCurrentPageSelected = posts.length > 0 && posts.every(post => selectedPosts.has(post.id));
  
  // Проверяем, выбраны ли некоторые посты на текущей странице
  const isSomeCurrentPageSelected = posts.some(post => selectedPosts.has(post.id));

  // Orphan cleanup functionality (existing)
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

  const togglePostExpansion = (postId) => {
    setExpandedPosts((prevExpandedPosts) => ({
      ...prevExpandedPosts,
      [postId]: !prevExpandedPosts[postId]
    }));
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
        
        <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
          <Box sx={{ width: '150px' }}>
            <TextField
              fullWidth
              label="Поиск по содержимому"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
          </Box>
          
          <Box sx={{ width: '180px' }}>
            <FormControl fullWidth>
              <InputLabel>Каналы</InputLabel>
              <Select
                value={channelFilter}
                onChange={(e) => setChannelFilter(e.target.value)}
                label="Каналы"
              >
                <MenuItem value="">Все каналы</MenuItem>
                {stats?.channels?.map((channel) => (
                  <MenuItem key={channel.telegram_id} value={channel.telegram_id}>
                    {channel.title || channel.channel_name} ({channel.posts_count})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
          
          <Box sx={{ width: '180px' }}>
            <FormControl fullWidth>
              <InputLabel>Статусы</InputLabel>
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                label="Статусы"
              >
                <MenuItem value="">Все статусы</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="processing">Processing</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
              </Select>
            </FormControl>
          </Box>
          
          <Box sx={{ flex: 1, minWidth: '180px' }}>
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
              <Button
                variant="outlined"
                color="error"
                onClick={() => setBulkDeleteConfirmDialog(true)}
                startIcon={<DeleteIcon />}
                disabled={selectedPosts.size === 0}
              >
                Удалить выделенные ({selectedPosts.size})
              </Button>
            </Box>
          </Box>
        </Box>
      </Paper>

      {/* Таблица постов */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  checked={isAllCurrentPageSelected}
                  indeterminate={!isAllCurrentPageSelected && isSomeCurrentPageSelected}
                  onChange={handleSelectAllPosts}
                  color="primary"
                />
              </TableCell>
              <TableCell>ID</TableCell>
              <TableCell>Канал</TableCell>
              <TableCell>Содержимое</TableCell>
              <TableCell>Просмотры</TableCell>
              <TableCell>Дата поста</TableCell>
              <TableCell>Собрано</TableCell>
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
                const isExpanded = expandedPosts[post.id];
                
                return (
                  <React.Fragment key={post.id}>
                    <TableRow hover>
                      <TableCell>
                        <Checkbox
                          checked={selectedPosts.has(post.id)}
                          onChange={() => handleSelectPost(post.id)}
                          color="primary"
                        />
                      </TableCell>
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
                        <Box sx={{ maxWidth: 600 }}>
                          {post.title && (
                            <Typography variant="body2" fontWeight="bold" gutterBottom>
                              {truncateText(post.title, 25)}
                            </Typography>
                          )}
                          <Typography variant="body2" color="text.secondary">
                            {truncateText(cleanMarkdownText(post.content), 50)}
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
                        <Box display="flex" gap={1}>
                          <Tooltip title="Просмотр в Telegram">
                            <IconButton
                              size="small"
                              onClick={() => window.open(`https://t.me/c/${Math.abs(post.channel_telegram_id)}/1${post.telegram_message_id}`, '_blank')}
                            >
                              <LinkIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title={isExpanded ? "Свернуть" : "Развернуть"}>
                            <IconButton size="small" onClick={() => togglePostExpansion(post.id)}>
                              {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                    
                    {/* Расширенная информация о посте */}
                    <TableRow>
                      <TableCell colSpan={7} sx={{ py: 0 }}>
                        <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                          <Box sx={{ p: 2, bgcolor: 'grey.50' }}>
                            <Grid container spacing={2}>
                              <Grid item xs={12} md={8}>
                                <Typography variant="subtitle2" gutterBottom>
                                  Полный текст поста:
                                </Typography>
                                {post.title && (
                                  <Typography variant="h6" gutterBottom>
                                    {post.title}
                                  </Typography>
                                )}
                                <Typography variant="body2" sx={{ mb: 2, whiteSpace: 'pre-wrap' }}>
                                  {post.content || 'Нет содержимого'}
                                </Typography>
                                
                                {post.media_urls && post.media_urls.length > 0 && (
                                  <Box>
                                    <Typography variant="subtitle2" gutterBottom>
                                      Медиа файлы ({post.media_urls.length}):
                                    </Typography>
                                    {post.media_urls.slice(0, 5).map((url, index) => (
                                      <Chip 
                                        key={index}
                                        label={`📎 Файл ${index + 1}`} 
                                        size="small" 
                                        sx={{ mr: 1, mb: 1 }}
                                        onClick={() => window.open(url, '_blank')}
                                        clickable
                                      />
                                    ))}
                                    {post.media_urls.length > 5 && (
                                      <Typography variant="caption" color="text.secondary">
                                        И еще {post.media_urls.length - 5} файлов...
                                      </Typography>
                                    )}
                                  </Box>
                                )}
                              </Grid>
                              
                              <Grid item xs={12} md={4}>
                                <Typography variant="subtitle2" gutterBottom>
                                  Техническая информация:
                                </Typography>
                                
                                <Box display="flex" flexDirection="column" gap={1}>
                                  <Typography variant="body2">
                                    <strong>ID поста:</strong> {post.id}
                                  </Typography>
                                  <Typography variant="body2">
                                    <strong>Telegram ID:</strong> {post.telegram_message_id}
                                  </Typography>
                                  <Typography variant="body2">
                                    <strong>Канал ID:</strong> {post.channel_telegram_id}
                                  </Typography>
                                  <Typography variant="body2">
                                    <strong>Просмотры:</strong> {formatViews(post.views)}
                                  </Typography>
                                  <Typography variant="body2">
                                    <strong>Дата поста:</strong> {formatDate(post.post_date)}
                                  </Typography>
                                  <Typography variant="body2">
                                    <strong>Собрано:</strong> {formatDate(post.collected_at)}
                                  </Typography>
                                </Box>
                                
                                <Box mt={2}>
                                  <Button
                                    variant="outlined"
                                    size="small"
                                    startIcon={<LinkIcon />}
                                    onClick={() => window.open(`https://t.me/c/${Math.abs(post.channel_telegram_id)}/1${post.telegram_message_id}`, '_blank')}
                                    fullWidth
                                  >
                                    Открыть в Telegram
                                  </Button>
                                </Box>
                              </Grid>
                            </Grid>
                          </Box>
                        </Collapse>
                      </TableCell>
                    </TableRow>
                  </React.Fragment>
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

      {/* Диалог подтверждения bulk delete */}
      <Dialog open={bulkDeleteConfirmDialog} onClose={() => setBulkDeleteConfirmDialog(false)}>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <DeleteIcon color="error" />
            Удаление выбранных постов
          </Box>
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Вы уверены, что хотите удалить {selectedPosts.size} выбранных постов?
            Это действие также удалит все связанные AI результаты и нельзя отменить.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBulkDeleteConfirmDialog(false)}>
            Отмена
          </Button>
          <Button
            onClick={handleBulkDelete}
            color="error"
            variant="contained"
            disabled={bulkDeleting}
            startIcon={bulkDeleting ? <CircularProgress size={20} /> : <DeleteIcon />}
          >
            {bulkDeleting ? 'Удаление...' : 'Удалить'}
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
      
      <Snackbar
        open={!!bulkDeleteSuccess}
        autoHideDuration={6000}
        onClose={() => setBulkDeleteSuccess('')}
        message={bulkDeleteSuccess}
      />
    </Box>
  );
}

export default RawPostsTab; 