import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  Chip,
  Button,
  Stack,
  Divider,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Snackbar,
  Tooltip,
  IconButton,
  Collapse
} from '@mui/material';

import {
  Assessment as AssessmentIcon,
  Psychology as PsychologyIcon,
  SmartToy as SmartToyIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Pending as PendingIcon,
  RestartAlt as RestartAltIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  ExpandLess as ExpandLessIcon,
  ExpandMore as ExpandMoreIcon
} from '@mui/icons-material';

const AIResultsPage = () => {
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState({ show: false, type: 'info', message: '' });
  const [botsWithStats, setBotsWithStats] = useState([]);
  const [expandedBot, setExpandedBot] = useState(null);
  const [orchestratorStatus, setOrchestratorStatus] = useState(null);

  // 🆕 ФУНКЦИЯ: Получение мультитенантной статистики по ботам
  const fetchBotsWithMultitenantStats = async () => {
    try {
      // 1. Получаем всех ботов
      const botsResponse = await fetch('http://localhost:8000/api/public-bots');
      if (!botsResponse.ok) throw new Error('Failed to fetch bots');
      const allBots = await botsResponse.json();
      
      // 2. Для каждого бота получаем детальную статистику
      const botsWithStatsPromises = allBots.map(async (bot) => {
        try {
          // AI результаты для этого бота
          const resultsResponse = await fetch(`http://localhost:8000/api/ai/results?bot_id=${bot.id}&limit=1000`);
          const results = resultsResponse.ok ? await resultsResponse.json() : [];
          
          // Каналы бота
          const channelsResponse = await fetch(`http://localhost:8000/api/public-bots/${bot.id}/channels`);
          const botChannels = channelsResponse.ok ? await channelsResponse.json() : [];
          
          // Категории бота
          const categoriesResponse = await fetch(`http://localhost:8000/api/public-bots/${bot.id}/categories`);
          const botCategories = categoriesResponse.ok ? await categoriesResponse.json() : [];
          
          // Статистика постов из каналов этого бота
          const channelTelegramIds = botChannels.map(ch => ch.telegram_id);
          let postsStats = { total: 0, pending: 0, processing: 0, completed: 0, failed: 0 };
          
          if (channelTelegramIds.length > 0) {
            const postsStatsPromises = channelTelegramIds.map(async (channelId) => {
              try {
                const statsResponse = await fetch(`http://localhost:8000/api/posts/cache?channel_telegram_id=${channelId}&limit=1000`);
                if (statsResponse.ok) {
                  const posts = await statsResponse.json();
                  return posts;
                }
                return [];
              } catch (error) {
                console.error(`Ошибка получения постов для канала ${channelId}:`, error);
                return [];
              }
            });
            
            const allChannelPosts = await Promise.all(postsStatsPromises);
            const flatPosts = allChannelPosts.flat();
            
            postsStats.total = flatPosts.length;
            postsStats.pending = flatPosts.filter(p => p.processing_status === 'pending').length;
            postsStats.processing = flatPosts.filter(p => p.processing_status === 'processing').length;
            postsStats.completed = flatPosts.filter(p => p.processing_status === 'completed').length;
            postsStats.failed = flatPosts.filter(p => p.processing_status === 'failed').length;
          }
          
          return {
            ...bot,
            ai_results_count: results.length,
            channels_count: botChannels.length,
            categories_count: botCategories.length,
            posts_stats: postsStats,
            last_ai_processing: results.length > 0 ? 
              Math.max(...results.map(r => new Date(r.processed_at).getTime())) : null,
            channels: botChannels,
            categories: botCategories,
            ai_results: results.slice(0, 5) // Последние 5 результатов для превью
          };
        } catch (error) {
          console.error(`Ошибка получения статистики для бота ${bot.id}:`, error);
          return {
            ...bot,
            ai_results_count: 0,
            channels_count: 0,
            categories_count: 0,
            posts_stats: { total: 0, pending: 0, processing: 0, completed: 0, failed: 0 },
            last_ai_processing: null,
            channels: [],
            categories: [],
            ai_results: []
          };
        }
      });
      
      const botsWithStats = await Promise.all(botsWithStatsPromises);
      setBotsWithStats(botsWithStats);
      
    } catch (error) {
      console.error('Ошибка получения мультитенантной статистики ботов:', error);
      setBotsWithStats([]);
      showAlert('error', 'Ошибка загрузки статистики ботов');
    }
  };

  // Получение статуса AI Orchestrator
  const fetchOrchestratorStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/orchestrator/live-status');
      if (response.ok) {
        const status = await response.json();
        setOrchestratorStatus(status);
      }
    } catch (error) {
      console.error('Ошибка получения статуса Orchestrator:', error);
    }
  };

  // Загрузка всех данных
  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchBotsWithMultitenantStats(),
        fetchOrchestratorStatus()
      ]);
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
      showAlert('error', 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  // Разворачивание/сворачивание деталей бота
  const handleBotExpand = (botId) => {
    setExpandedBot(expandedBot === botId ? null : botId);
  };

  // Показ уведомления
  const showAlert = (type, message) => {
    setAlert({ show: true, type, message });
  };

  // Форматирование даты
  const formatDate = (timestamp) => {
    if (!timestamp) return 'Никогда';
    return new Date(timestamp).toLocaleString('ru-RU');
  };

  // Инициализация
  useEffect(() => {
    loadData();
    // Автообновление каждые 15 секунд
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="50vh">
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Загрузка мультитенантной статистики...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Заголовок */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            <AssessmentIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
            AI Результаты - Мультитенантная архитектура
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Статистика обработки AI по ботам • Обновлено: {new Date().toLocaleString('ru-RU')}
          </Typography>
        </Box>
        
        <Box display="flex" gap={2} alignItems="center">
          {/* Статус AI Orchestrator */}
          {orchestratorStatus ? (
            <Chip
              label={orchestratorStatus.orchestrator_active ? "AI Orchestrator: АКТИВЕН" : "AI Orchestrator: НЕ АКТИВЕН"}
              color={orchestratorStatus.orchestrator_active ? "success" : "error"}
              icon={<SmartToyIcon />}
            />
          ) : (
            <Chip label="AI Orchestrator: НЕИЗВЕСТНО" color="warning" />
          )}
          
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadData}
            disabled={loading}
          >
            Обновить
          </Button>
        </Box>
      </Box>

      {/* Alert */}
      <Snackbar 
        open={alert.show} 
        autoHideDuration={6000} 
        onClose={() => setAlert({ show: false, type: 'info', message: '' })}
      >
        <Alert severity={alert.type} onClose={() => setAlert({ show: false, type: 'info', message: '' })}>
          {alert.message}
        </Alert>
      </Snackbar>

      {/* 🚀 ГЛАВНАЯ ТАБЛИЦА: МУЛЬТИТЕНАНТНАЯ СТАТИСТИКА ПО БОТАМ */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <SmartToyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Статистика по ботам ({botsWithStats.length})
          </Typography>
          
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Каждый бот обрабатывает посты из своих каналов с индивидуальными категориями и настройками AI
          </Typography>

          {botsWithStats.length > 0 ? (
            <TableContainer component={Paper} variant="outlined" sx={{ mt: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Бот</strong></TableCell>
                    <TableCell align="center"><strong>AI Результаты</strong></TableCell>
                    <TableCell align="center"><strong>Каналы</strong></TableCell>
                    <TableCell align="center"><strong>Категории</strong></TableCell>
                    <TableCell align="center"><strong>Всего постов</strong></TableCell>
                    <TableCell align="center"><strong>Ожидают</strong></TableCell>
                    <TableCell align="center"><strong>Обработка</strong></TableCell>
                    <TableCell align="center"><strong>Готово</strong></TableCell>
                    <TableCell align="center"><strong>Ошибки</strong></TableCell>
                    <TableCell align="center"><strong>Прогресс</strong></TableCell>
                    <TableCell align="center"><strong>Детали</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {botsWithStats.map((bot) => (
                    <React.Fragment key={bot.id}>
                      {/* Основная строка бота */}
                      <TableRow hover>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" fontWeight="bold">
                              {bot.name}
                            </Typography>
                            <Box display="flex" gap={1} mt={0.5}>
                              <Chip 
                                label={bot.status} 
                                color={bot.status === 'active' ? 'success' : 'info'} 
                                size="small" 
                              />
                              {bot.last_ai_processing && (
                                <Chip 
                                  label={`${formatDate(bot.last_ai_processing).split(' ')[0]}`}
                                  size="small"
                                  variant="outlined"
                                />
                              )}
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell align="center">
                          <Typography variant="h6" color="primary" fontWeight="bold">
                            {bot.ai_results_count}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Chip 
                            label={bot.channels_count} 
                            color={bot.channels_count > 0 ? "success" : "default"} 
                            size="small" 
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Chip 
                            label={bot.categories_count} 
                            color={bot.categories_count > 0 ? "success" : "default"} 
                            size="small" 
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Typography variant="body2" fontWeight="bold">
                            {bot.posts_stats.total}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Chip 
                            label={bot.posts_stats.pending} 
                            color={bot.posts_stats.pending > 0 ? "warning" : "default"} 
                            size="small" 
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Chip 
                            label={bot.posts_stats.processing} 
                            color={bot.posts_stats.processing > 0 ? "info" : "default"} 
                            size="small" 
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Chip 
                            label={bot.posts_stats.completed} 
                            color="success" 
                            size="small" 
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Chip 
                            label={bot.posts_stats.failed} 
                            color={bot.posts_stats.failed > 0 ? "error" : "default"} 
                            size="small" 
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Box display="flex" alignItems="center" gap={1}>
                            <LinearProgress 
                              variant="determinate" 
                              value={bot.posts_stats.total > 0 ? 
                                Math.round((bot.posts_stats.completed / bot.posts_stats.total) * 100) : 0} 
                              sx={{ width: 60, height: 8 }}
                              color={bot.posts_stats.completed === bot.posts_stats.total ? "success" : "primary"}
                            />
                            <Typography variant="caption" fontWeight="bold">
                              {bot.posts_stats.total > 0 ? 
                                Math.round((bot.posts_stats.completed / bot.posts_stats.total) * 100) : 0}%
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell align="center">
                          <IconButton
                            size="small"
                            onClick={() => handleBotExpand(bot.id)}
                            disabled={bot.channels_count === 0 && bot.ai_results_count === 0}
                          >
                            {expandedBot === bot.id ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                          </IconButton>
                        </TableCell>
                      </TableRow>

                      {/* Развернутые детали бота */}
                      <TableRow>
                        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={11}>
                          <Collapse in={expandedBot === bot.id} timeout="auto" unmountOnExit>
                            <Box sx={{ margin: 2, bgcolor: 'background.paper', p: 2, borderRadius: 1 }}>
                              <Typography variant="h6" gutterBottom>
                                🔍 Детали бота: {bot.name}
                              </Typography>
                              
                              <Grid container spacing={3}>
                                {/* Каналы бота */}
                                <Grid item xs={12} md={6}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    📺 Каналы ({bot.channels.length}):
                                  </Typography>
                                  {bot.channels.length > 0 ? (
                                    <Stack spacing={1}>
                                      {bot.channels.map((channel) => (
                                        <Box key={channel.id} display="flex" alignItems="center" gap={1}>
                                          <Chip
                                            label={channel.username || channel.channel_name}
                                            size="small"
                                            variant="outlined"
                                            color="primary"
                                          />
                                          <Typography variant="caption" color="text.secondary">
                                            ID: {channel.telegram_id}
                                          </Typography>
                                        </Box>
                                      ))}
                                    </Stack>
                                  ) : (
                                    <Typography variant="body2" color="text.secondary">
                                      Нет настроенных каналов
                                    </Typography>
                                  )}
                                </Grid>
                                
                                {/* Категории бота */}
                                <Grid item xs={12} md={6}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    📂 Категории ({bot.categories.length}):
                                  </Typography>
                                  {bot.categories.length > 0 ? (
                                    <Stack spacing={1}>
                                      {bot.categories.map((category) => (
                                        <Box key={category.id} display="flex" alignItems="center" gap={1}>
                                          <Chip
                                            label={category.category_name}
                                            size="small"
                                            color="secondary"
                                            variant="outlined"
                                          />
                                          <Typography variant="caption" color="text.secondary">
                                            Вес: {category.weight || 'N/A'}
                                          </Typography>
                                        </Box>
                                      ))}
                                    </Stack>
                                  ) : (
                                    <Typography variant="body2" color="text.secondary">
                                      Нет настроенных категорий
                                    </Typography>
                                  )}
                                </Grid>

                                {/* Последние AI результаты */}
                                <Grid item xs={12}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    🧠 Последние AI результаты ({bot.ai_results.length} из {bot.ai_results_count}):
                                  </Typography>
                                  {bot.ai_results.length > 0 ? (
                                    <TableContainer component={Paper} variant="outlined" size="small">
                                      <Table size="small">
                                        <TableHead>
                                          <TableRow>
                                            <TableCell>Пост ID</TableCell>
                                            <TableCell>Категория</TableCell>
                                            <TableCell>Релевантность</TableCell>
                                            <TableCell>Обработано</TableCell>
                                          </TableRow>
                                        </TableHead>
                                        <TableBody>
                                          {bot.ai_results.map((result, index) => (
                                            <TableRow key={index}>
                                              <TableCell>
                                                <Typography variant="caption">
                                                  {result.post_id}
                                                </Typography>
                                              </TableCell>
                                              <TableCell>
                                                <Chip
                                                  label={result.category || 'NULL'}
                                                  size="small"
                                                  color={result.category ? 'success' : 'default'}
                                                />
                                              </TableCell>
                                              <TableCell>
                                                <Typography variant="caption">
                                                  {result.relevance_score ? `${(result.relevance_score * 100).toFixed(1)}%` : 'N/A'}
                                                </Typography>
                                              </TableCell>
                                              <TableCell>
                                                <Typography variant="caption">
                                                  {formatDate(result.processed_at)}
                                                </Typography>
                                              </TableCell>
                                            </TableRow>
                                          ))}
                                        </TableBody>
                                      </Table>
                                    </TableContainer>
                                  ) : (
                                    <Typography variant="body2" color="text.secondary">
                                      Нет AI результатов
                                    </Typography>
                                  )}
                                </Grid>
                              </Grid>

                              {/* Кнопки управления */}
                              <Box display="flex" gap={1} mt={2}>
                                <Button
                                  size="small"
                                  variant="outlined"
                                  startIcon={<RestartAltIcon />}
                                  onClick={() => {
                                    showAlert('info', `Переобработка бота ${bot.name} - функция в разработке`);
                                  }}
                                >
                                  Переобработать
                                </Button>
                                <Button
                                  size="small"
                                  variant="outlined"
                                  startIcon={<VisibilityIcon />}
                                  onClick={() => {
                                    showAlert('info', `Просмотр результатов бота ${bot.name} - функция в разработке`);
                                  }}
                                >
                                  Все результаты
                                </Button>
                              </Box>
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>
                    </React.Fragment>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Box textAlign="center" py={4}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Нет данных по ботам
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Проверьте подключение к Backend API
              </Typography>
            </Box>
          )}

          {/* Итоговая статистика */}
          {botsWithStats.length > 0 && (
            <Box mt={3} p={2} bgcolor="background.paper" borderRadius={1}>
              <Typography variant="h6" gutterBottom>
                📊 Итоговая статистика системы:
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Typography variant="body2" color="text.secondary">Всего ботов:</Typography>
                  <Typography variant="h6">{botsWithStats.length}</Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="body2" color="text.secondary">AI результатов:</Typography>
                  <Typography variant="h6" color="primary">
                    {botsWithStats.reduce((sum, bot) => sum + bot.ai_results_count, 0)}
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="body2" color="text.secondary">Всего постов:</Typography>
                  <Typography variant="h6">
                    {botsWithStats.reduce((sum, bot) => sum + bot.posts_stats.total, 0)}
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="body2" color="text.secondary">Готово:</Typography>
                  <Typography variant="h6" color="success.main">
                    {botsWithStats.reduce((sum, bot) => sum + bot.posts_stats.completed, 0)}
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default AIResultsPage; 