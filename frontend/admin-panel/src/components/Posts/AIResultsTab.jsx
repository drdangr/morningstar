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
  Divider
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
  SmartToy as SmartToyIcon
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
  const [sortBy, setSortBy] = useState('collected_at');
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
  }, [page, rowsPerPage, selectedBotId, search, channelFilter, aiStatusFilter, dateFrom, dateTo, sortBy, sortOrder]);

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
                  {posts.filter(p => p.ai_summary || p.ai_category).length} из {posts.length}
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
                  {posts.filter(p => p.ai_is_categorized && p.ai_is_summarized).length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Средняя важность
                </Typography>
                <Typography variant="h6">
                  {posts.length > 0 ? 
                    (posts.filter(p => p.ai_importance).reduce((sum, p) => sum + (p.ai_importance || 0), 0) / 
                     posts.filter(p => p.ai_importance).length).toFixed(1) : 
                    'N/A'
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
                <TableCell colSpan={6} align="center">
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : posts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography color="text.secondary">
                    {selectedBotId ? 'Нет AI результатов для выбранного бота' : 'Выберите бота для просмотра результатов'}
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
                      
                      <TableCell>
                        {post.ai_category ? (
                          <Chip 
                            label={post.ai_category} 
                            color="primary" 
                            icon={<CategoryIcon />}
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
                            <Box display="flex" alignItems="center" gap={1}>
                              <Typography variant="caption">Важность:</Typography>
                              <Rating 
                                value={post.ai_importance / 2} 
                                max={5} 
                                size="small" 
                                readOnly 
                              />
                              <Typography variant="caption">
                                {formatAIMetric(post.ai_importance)}
                              </Typography>
                            </Box>
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
                          <Tooltip title="Просмотр в Telegram">
                            <IconButton
                              size="small"
                              onClick={() => window.open(`https://t.me/c/${Math.abs(post.channel_telegram_id)}/1${post.telegram_message_id}`, '_blank')}
                            >
                              <LinkIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title={isExpanded ? "Свернуть" : "Развернуть"}>
                            <IconButton
                              size="small"
                              onClick={() => togglePostExpansion(post.id)}
                            >
                              {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
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
                                      Summary:
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
    </Box>
  );
}

export default AIResultsTab; 