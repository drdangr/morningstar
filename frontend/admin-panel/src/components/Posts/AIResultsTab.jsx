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
  Rating,
  Collapse,
  Divider,
  Checkbox,
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
  Psychology as PsychologyIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Category as CategoryIcon,
  TrendingUp as TrendingUpIcon,
  SmartToy as SmartToyIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';

// Импорт компонента выбора бота
import BotSelector from './BotSelector';

// Определяем API URL динамически
const API_BASE_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000' 
  : 'http://localhost:8000';

function AIResultsTab({ stats, onStatsUpdate }) {
  // Состояние для данных
  const [posts, setPosts] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [aiStats, setAiStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Состояние для расширенного отображения
  const [expandedPosts, setExpandedPosts] = useState(new Set());

  // Состояние для bulk delete функциональности
  const [selectedPosts, setSelectedPosts] = useState(new Set());
  const [bulkDeleteConfirmDialog, setBulkDeleteConfirmDialog] = useState(false);
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [bulkDeleteSuccess, setBulkDeleteSuccess] = useState('');

  // Состояние для фильтров
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [selectedBotId, setSelectedBotId] = useState(''); // Мультитенантный фильтр
  const [search, setSearch] = useState('');
  const [channelFilter, setChannelFilter] = useState('');
  const [aiStatusFilter, setAiStatusFilter] = useState('all'); // all, processed, unprocessed
  const [categoryFilter, setCategoryFilter] = useState('');
  const [dateFrom, setDateFrom] = useState(null);
  const [dateTo, setDateTo] = useState(null);
  const [sortBy, setSortBy] = useState('post_date');
  const [sortOrder, setSortOrder] = useState('desc');

  // Загрузка AI статистики
  const loadAIStats = async () => {
    try {
      console.log('🔄 Загружаем AI статистику...');
      const response = await fetch(`${API_BASE_URL}/api/ai/multitenant-status`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ AI статистика загружена:', data);
      setAiStats(data);
      
      // Устанавливаем первого активного бота по умолчанию
      if (data.bots_stats && data.bots_stats.length > 0 && !selectedBotId) {
        const activeBots = data.bots_stats.filter(bot => bot.status === 'active');
        if (activeBots.length > 0) {
          setSelectedBotId(activeBots[0].bot_id.toString());
        } else {
          // Если нет активных ботов, берем первого доступного
          setSelectedBotId(data.bots_stats[0].bot_id.toString());
        }
      }
    } catch (err) {
      console.error('❌ Ошибка загрузки AI статистики:', err);
    }
  };

  // Загрузка AI результатов с мультитенантной фильтрацией
  const loadAIResults = async () => {
    setLoading(true);
    setError('');

    try {
      console.log('🔄 Загружаем AI результаты для бота:', selectedBotId);
      
      // Параметры запроса
      const params = new URLSearchParams({
        skip: page * rowsPerPage,
        limit: rowsPerPage,
        sort_by: sortBy,
        sort_order: sortOrder,
        ai_status: aiStatusFilter
      });

      // 🚀 НОВЫЙ ФИЛЬТР: bot_id для мультитенантности
      if (selectedBotId) params.append('bot_id', selectedBotId);
      
      if (search) params.append('search', search);
      if (channelFilter) params.append('channel_telegram_id', channelFilter);
      if (categoryFilter) params.append('ai_category', categoryFilter);
      if (dateFrom) params.append('date_from', dateFrom.toISOString());
      if (dateTo) params.append('date_to', dateTo.toISOString());

      // Используем endpoint /api/posts/cache-with-ai с bot_id фильтром
      const response = await fetch(`${API_BASE_URL}/api/posts/cache-with-ai?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ AI результаты загружены:', data.posts?.length || 0);
      
      setPosts(data.posts || []);
      setTotalCount(data.total_count || 0);
    } catch (err) {
      console.error('❌ Ошибка загрузки AI результатов:', err);
      setError('Ошибка загрузки AI результатов: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Загрузка данных при изменении фильтров
  useEffect(() => {
    if (selectedBotId) {
      loadAIResults();
    }
  }, [page, rowsPerPage, selectedBotId, search, channelFilter, categoryFilter, aiStatusFilter, dateFrom, dateTo, sortBy, sortOrder]);

  // Очистка выбранных постов при смене страницы или фильтров
  useEffect(() => {
    clearSelectedPosts();
  }, [page, rowsPerPage, selectedBotId, search, channelFilter, categoryFilter, aiStatusFilter, dateFrom, dateTo, sortBy, sortOrder]);

  // Загрузка ботов и AI статистики при монтировании
  useEffect(() => {
    loadAIStats();
  }, []);

  // Обработчики событий
  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  const handleRowsPerPageChange = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleBotChange = (botId) => {
    setSelectedBotId(botId ? botId.toString() : '');
    setPage(0); // Сбрасываем страницу при смене бота
  };

  const handleClearFilters = () => {
    setSearch('');
    setChannelFilter('');
    setCategoryFilter('');
    setDateFrom(null);
    setDateTo(null);
    setPage(0);
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
      // 🧠 ИСПОЛЬЗУЕМ СПЕЦИАЛЬНЫЙ ENDPOINT ДЛЯ УДАЛЕНИЯ ТОЛЬКО AI РЕЗУЛЬТАТОВ
      const response = await fetch(`${API_BASE_URL}/api/ai/results/bulk-delete`, {
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
        throw new Error(errorData.detail || 'Ошибка удаления AI результатов');
      }

      const result = await response.json();
      
      // Успешное удаление AI результатов
      setBulkDeleteSuccess(
        `Удалены AI результаты для ${result.posts_preserved} постов (${result.deleted_ai_results} записей)`
      );
      setSelectedPosts(new Set());
      setBulkDeleteConfirmDialog(false);
      
      // Обновляем данные
      loadAIResults();
      if (onStatsUpdate) onStatsUpdate();
      
    } catch (err) {
      console.error('❌ Ошибка bulk delete AI результатов:', err);
      setError('Ошибка удаления AI результатов: ' + err.message);
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

  const togglePostExpansion = (postId) => {
    const newExpanded = new Set(expandedPosts);
    if (newExpanded.has(postId)) {
      newExpanded.delete(postId);
    } else {
      newExpanded.add(postId);
    }
    setExpandedPosts(newExpanded);
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

  const getAIStatusColor = (post) => {
    if (post.ai_is_categorized && post.ai_is_summarized) return 'success';
    if (post.ai_is_categorized || post.ai_is_summarized) return 'warning';
    return 'default';
  };

  const getAIStatusText = (post) => {
    if (post.ai_is_categorized && post.ai_is_summarized) return 'Полностью обработан';
    if (post.ai_is_categorized && !post.ai_is_summarized) return 'Только категоризирован';
    if (!post.ai_is_categorized && post.ai_is_summarized) return 'Только саммаризирован';
    return 'Не обработан';
  };

  const formatAIMetric = (value) => {
    if (value === null || value === undefined) return 'N/A';
    return typeof value === 'number' ? value.toFixed(1) : value;
  };

  // Получение уникальных категорий из загруженных постов
  const getUniqueCategories = () => {
    const categories = posts
      .filter(post => post.ai_category && post.ai_category.trim() !== '')
      .map(post => post.ai_category.trim())
      .filter((category, index, array) => array.indexOf(category) === index)
      .sort();
    return categories;
  };

  const selectedBot = aiStats?.bots_stats.find(bot => bot.bot_id === parseInt(selectedBotId));

  return (
    <Box>
      {/* Заголовок таба */}
      <Box display="flex" alignItems="center" gap={2} sx={{ mb: 3 }}>
        <PsychologyIcon color="secondary" />
        <Typography variant="h5">
          AI RESULTS - Мультитенантные результаты
        </Typography>
        <Chip 
          label={`${totalCount.toLocaleString()} результатов`} 
          color="secondary" 
          variant="outlined" 
        />
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        AI результаты с мультитенантной фильтрацией по ботам. Отображение summary, категорий, метрик и статусов обработки.
      </Typography>

      {/* Выбор бота для мультитенантной фильтрации */}
      <BotSelector 
        selectedBot={selectedBotId ? parseInt(selectedBotId) : null}
        onBotChange={handleBotChange}
        aiStats={aiStats}
      />

      {/* Статистика AI результатов */}
      {selectedBotId && aiStats && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Выбранный бот
                </Typography>
                <Typography variant="h6">
                  {selectedBot?.name || 'Неизвестный бот'}
                </Typography>
                <Chip 
                  label={selectedBot?.status === 'active' ? 'Активен' : 'Неактивен'} 
                  size="small" 
                  color={selectedBot?.status === 'active' ? 'success' : 'default'}
                />
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  AI результатов
                </Typography>
                <Typography variant="h6">
                  {selectedBot?.multitenant_stats?.completed || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Полностью обработано
                </Typography>
                <Typography variant="h6">
                  {selectedBot?.multitenant_stats?.completed || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  В обработке
                </Typography>
                <Typography variant="h6">
                  {selectedBot?.multitenant_stats ? 
                    (selectedBot.multitenant_stats.pending + selectedBot.multitenant_stats.processing) : 
                    0
                  }
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Ошибки */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Фильтры */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Фильтры AI результатов
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
              <InputLabel>AI Категории</InputLabel>
              <Select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                label="AI Категории"
              >
                <MenuItem value="">Все категории</MenuItem>
                {getUniqueCategories().map((category) => (
                  <MenuItem key={category} value={category}>
                    {category}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
          
          <Box sx={{ width: '180px' }}>
            <FormControl fullWidth>
              <InputLabel>AI Статусы</InputLabel>
              <Select
                value={aiStatusFilter}
                onChange={(e) => setAiStatusFilter(e.target.value)}
                label="AI Статусы"
              >
                <MenuItem value="all">Все результаты</MenuItem>
                <MenuItem value="processed">Обработанные</MenuItem>
                <MenuItem value="unprocessed">Необработанные</MenuItem>
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
                onClick={loadAIResults}
                startIcon={<RefreshIcon />}
                disabled={loading}
              >
                Обновить
              </Button>
              <Button
                variant="outlined"
                color="error"
                onClick={() => setBulkDeleteConfirmDialog(true)}
                startIcon={<SmartToyIcon />}
                disabled={selectedPosts.size === 0}
              >
                Очистить AI данные ({selectedPosts.size})
              </Button>
            </Box>
          </Box>
        </Box>
      </Paper>

      {/* Предупреждение если бот не выбран */}
      {!selectedBotId && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography>
            Выберите бота для просмотра AI результатов. Каждый бот имеет свои индивидуальные результаты обработки.
          </Typography>
        </Alert>
      )}

      {/* Таблица AI результатов */}
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
              <TableCell>Пост</TableCell>
              <TableCell>AI Категория</TableCell>
              <TableCell>AI Summary</TableCell>
              <TableCell>Метрики</TableCell>
              <TableCell>AI Статус</TableCell>
              <TableCell>Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : posts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography color="text.secondary">
                    {selectedBotId ? 'Нет данных для отображения' : 'Выберите бота для просмотра AI результатов'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              posts.map((post) => {
                const channelInfo = getChannelInfo(post.channel_telegram_id);
                const isExpanded = expandedPosts.has(post.id);
                
                return (
                  <React.Fragment key={post.id}>
                    <TableRow hover>
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={selectedPosts.has(post.id)}
                          onChange={() => handleSelectPost(post.id)}
                          color="primary"
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ maxWidth: 500 }}>
                          <Typography variant="body2" fontWeight="bold" gutterBottom>
                            {channelInfo.title}
                          </Typography>
                          {post.title && (
                            <Typography variant="body2" color="primary" gutterBottom>
                              {truncateText(post.title, 20)}
                            </Typography>
                          )}
                          <Typography variant="body2" color="text.secondary">
                            {truncateText(cleanMarkdownText(post.content), 30)}
                          </Typography>
                          <Box display="flex" gap={1} mt={1}>
                            <Chip label={`👁 ${formatViews(post.views)}`} size="small" />
                            <Chip label={`ID: ${post.id}`} size="small" variant="outlined" />
                          </Box>
                        </Box>
                      </TableCell>
                      
                      <TableCell sx={{ maxWidth: 120 }}>
                        {post.ai_category ? (
                          <Chip 
                            label={post.ai_category} 
                            color="primary" 
                            icon={<CategoryIcon />}
                            sx={{ 
                              whiteSpace: 'normal',
                              wordBreak: 'normal',
                              overflowWrap: 'break-word',
                              height: 'auto',
                              '& .MuiChip-label': {
                                whiteSpace: 'normal',
                                wordBreak: 'normal',
                                overflowWrap: 'break-word',
                                lineHeight: 1.2,
                                padding: '4px 8px'
                              }
                            }}
                          />
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            Не категоризирован
                          </Typography>
                        )}
                      </TableCell>
                      
                      <TableCell>
                        <Box sx={{ maxWidth: 600 }}>
                          {post.ai_summary ? (
                            <Typography variant="body2">
                              {truncateText(post.ai_summary, 50)}
                            </Typography>
                          ) : (
                            <Typography variant="body2" color="text.secondary">
                              Нет summary
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Box display="flex" flexDirection="column" gap={0.5}>
                          {post.ai_importance && (
                            <Typography variant="caption" color="text.secondary">
                              Важность: {formatAIMetric(post.ai_importance)}
                            </Typography>
                          )}
                          {post.ai_urgency && (
                            <Typography variant="caption" color="text.secondary">
                              Срочность: {formatAIMetric(post.ai_urgency)}
                            </Typography>
                          )}
                          {post.ai_significance && (
                            <Typography variant="caption" color="text.secondary">
                              Значимость: {formatAIMetric(post.ai_significance)}
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Chip 
                          label={getAIStatusText(post)}
                          color={getAIStatusColor(post)}
                          size="small"
                        />
                        {post.ai_processed_at && (
                          <Typography variant="caption" display="block" color="text.secondary">
                            {formatDate(post.ai_processed_at)}
                          </Typography>
                        )}
                      </TableCell>
                      
                      <TableCell>
                        <Box display="flex" gap={1}>
                          <Tooltip title={isExpanded ? "Свернуть" : "Развернуть"}>
                            <IconButton
                              size="small"
                              onClick={() => togglePostExpansion(post.id)}
                            >
                              {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Просмотр в Telegram">
                            <IconButton
                              size="small"
                              onClick={() => window.open(`https://t.me/c/${Math.abs(post.channel_telegram_id)}/1${post.telegram_message_id}`, '_blank')}
                            >
                              <LinkIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                    
                    {/* Расширенная информация */}
                    <TableRow>
                      <TableCell colSpan={6} sx={{ py: 0 }}>
                        <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                          <Box sx={{ p: 2, bgcolor: 'grey.50' }}>
                            <Grid container spacing={2}>
                              <Grid item xs={12} md={6}>
                                <Typography variant="subtitle2" gutterBottom>
                                  Полный текст поста:
                                </Typography>
                                <Typography variant="body2" sx={{ mb: 2 }}>
                                  {post.content || 'Нет содержимого'}
                                </Typography>
                                
                                {post.media_urls && post.media_urls.length > 0 && (
                                  <Box>
                                    <Typography variant="subtitle2" gutterBottom>
                                      Медиа файлы ({post.media_urls.length}):
                                    </Typography>
                                    {post.media_urls.slice(0, 3).map((url, index) => (
                                      <Chip 
                                        key={index}
                                        label={`📎 Файл ${index + 1}`} 
                                        size="small" 
                                        sx={{ mr: 1, mb: 1 }}
                                        onClick={() => window.open(url, '_blank')}
                                      />
                                    ))}
                                  </Box>
                                )}
                              </Grid>
                              
                              <Grid item xs={12} md={6}>
                                <Typography variant="subtitle2" gutterBottom>
                                  AI Обработка:
                                </Typography>
                                
                                {post.ai_summary && (
                                  <Box sx={{ mb: 2 }}>
                                    <Typography variant="body2" fontWeight="bold">
                                      AI Summary:
                                    </Typography>
                                    <Typography variant="body2">
                                      {post.ai_summary}
                                    </Typography>
                                  </Box>
                                )}
                                
                                <Box display="flex" gap={1} flexWrap="wrap">
                                  <Chip 
                                    label={`Категоризирован: ${post.ai_is_categorized ? 'Да' : 'Нет'}`}
                                    color={post.ai_is_categorized ? 'success' : 'default'}
                                    size="small"
                                  />
                                  <Chip 
                                    label={`Саммаризирован: ${post.ai_is_summarized ? 'Да' : 'Нет'}`}
                                    color={post.ai_is_summarized ? 'success' : 'default'}
                                    size="small"
                                  />
                                  {post.ai_processing_version && (
                                    <Chip 
                                      label={`Версия: ${post.ai_processing_version}`}
                                      size="small"
                                      variant="outlined"
                                    />
                                  )}
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

      {/* Диалог подтверждения bulk delete */}
      <Dialog open={bulkDeleteConfirmDialog} onClose={() => setBulkDeleteConfirmDialog(false)}>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <SmartToyIcon color="error" />
            Очистка AI результатов
          </Box>
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Вы уверены, что хотите удалить AI результаты для {selectedPosts.size} выбранных постов?
            <br /><br />
            <strong>⚠️ Важно:</strong> Будут удалены только AI данные (категории, summary, метрики). 
            Оригинальные посты останутся в системе.
            <br /><br />
            Это действие нельзя отменить.
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
            startIcon={bulkDeleting ? <CircularProgress size={20} /> : <SmartToyIcon />}
          >
            {bulkDeleting ? 'Очистка...' : 'Очистить AI данные'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar для успешных операций */}
      <Snackbar
        open={!!bulkDeleteSuccess}
        autoHideDuration={6000}
        onClose={() => setBulkDeleteSuccess('')}
        message={bulkDeleteSuccess}
      />
    </Box>
  );
}

export default AIResultsTab; 