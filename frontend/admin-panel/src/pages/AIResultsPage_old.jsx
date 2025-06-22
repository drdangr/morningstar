import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  Tab,
  Tabs,
  TextField,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Rating,
  Divider,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Stack,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  FormGroup,
  Snackbar,
  Collapse
} from '@mui/material';
import {
  SmartToy as SmartToyIcon,
  Preview as PreviewIcon,
  Analytics as AnalyticsIcon,
  Speed as ProcessingIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as ViewIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Delete as DeleteIcon,
  Assessment as AssessmentIcon,
  Psychology as PsychologyIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Pending as PendingIcon,
  RestartAlt as RestartAltIcon,
  Tune as TuneIcon,
  Pause as PauseIcon,
  ExpandLess as ExpandLessIcon,
  ExpandMore as ExpandMoreIconTable,
  Settings as SettingsIcon,
  Build as BuildIcon
} from '@mui/icons-material';

// Mock data для демонстрации компонента
const mockAIResults = {
  totalProcessed: 51,
  totalPending: 0,
  averageQuality: 8.2,
  processingTime: '2.3s',
  lastUpdated: new Date().toISOString(),
  recentResults: [
    {
      id: 1,
      postTitle: 'Украинские дроны атаковали нефтезавод в Туле',
      originalContent: 'Украинские беспилотники атаковали нефтеперерабатывающий завод в Туле...',
      aiSummary: 'Атака беспилотников на нефтезавод в Туле: подробности инцидента и его последствия',
      aiCategory: 'Война',
      relevanceScore: 0.95,
      importanceScore: 8.5,
      urgencyScore: 9.0,
      qualityRating: null,
      processedAt: new Date(Date.now() - 3600000).toISOString(),
      channel: '@breakingmash'
    },
    {
      id: 2,
      postTitle: 'Павел Дуров объявил о новых функциях Telegram',
      originalContent: 'Основатель Telegram Павел Дуров анонсировал релиз новых функций...',
      aiSummary: 'Telegram получит новые функции: анонс от Павла Дурова',
      aiCategory: 'Технологии',
      relevanceScore: 0.78,
      importanceScore: 6.5,
      urgencyScore: 4.0,
      qualityRating: 4,
      processedAt: new Date(Date.now() - 7200000).toISOString(),
      channel: '@durov'
    }
  ]
};

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`ai-results-tabpanel-${index}`}
      aria-labelledby={`ai-results-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const AIResultsPage = () => {
  const [loading, setLoading] = useState(true);
  const [aiStatus, setAiStatus] = useState(null);
  const [activeTasks, setActiveTasks] = useState([]);
  const [detailedStatus, setDetailedStatus] = useState(null);
  const [detailedTabValue, setDetailedTabValue] = useState(0);
  const [channels, setChannels] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);
  const [actionLoading, setActionLoading] = useState(false);
  const [alert, setAlert] = useState({ show: false, type: 'info', message: '' });
  const [confirmDialog, setConfirmDialog] = useState({ open: false, action: null, title: '', message: '' });
  const [detailedStats, setDetailedStats] = useState(null);
  const [orchestratorLiveStatus, setOrchestratorLiveStatus] = useState(null);
  
  // 🆕 МУЛЬТИТЕНАНТНЫЕ СОСТОЯНИЯ
  const [bots, setBots] = useState([]);
  const [selectedBot, setSelectedBot] = useState('all');
  const [aiResults, setAiResults] = useState([]);
  const [botsWithStats, setBotsWithStats] = useState([]); // Статистика по ботам
  const [expandedBot, setExpandedBot] = useState(null); // Развернутый бот для drill-down
  const [botChannelsStats, setBotChannelsStats] = useState({}); // Статистика каналов по ботам

  useEffect(() => {
    const fetchAllData = async () => {
      setLoading(true);
      try {
        await Promise.all([
          fetchAIStatus(),
          fetchDetailedStatus(),
          fetchActiveTasks(),
          fetchChannels(),
          fetchOrchestratorLiveStatus(),
          fetchBotsWithMultitenantStats() // 🆕 Новая функция
        ]);
      } catch (error) {
        console.error('Ошибка загрузки данных:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAllData();
    
    // Автообновление каждые 5 секунд
    const interval = setInterval(async () => {
      try {
        await Promise.all([
          fetchAIStatus(),
          fetchDetailedStatus(),
          fetchActiveTasks(),
          fetchChannels(),
          fetchOrchestratorLiveStatus(),
          fetchBotsWithMultitenantStats() // 🆕 Новая функция
        ]);
      } catch (error) {
        console.error('Ошибка автообновления:', error);
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchAIStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/status');
      if (response.ok) {
        const data = await response.json();
        setAiStatus(data);
      } else {
        console.warn('Не удалось получить статус AI:', response.status);
        // Устанавливаем fallback данные
        setAiStatus({
          posts_stats: { total: 0, pending: 0, processing: 0, completed: 0, failed: 0 },
          ai_results_stats: { total_results: 0, results_per_post: 0 },
          bots_stats: { total_processing_bots: 0, active_bots: 0, development_bots: 0 }
        });
      }
    } catch (error) {
      console.error('Ошибка загрузки статуса AI:', error);
      // Устанавливаем fallback данные
      setAiStatus({
        posts_stats: { total: 0, pending: 0, processing: 0, completed: 0, failed: 0 },
        ai_results_stats: { total_results: 0, results_per_post: 0 },
        bots_stats: { total_processing_bots: 0, active_bots: 0, development_bots: 0 }
      });
    }
  };

  const fetchDetailedStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/detailed-status');
      if (response.ok) {
        const data = await response.json();
        setDetailedStatus(data);
      } else {
        console.warn('Не удалось получить детальную статистику AI:', response.status);
        // Устанавливаем fallback данные
        setDetailedStatus({
          total_channels: 0,
          total_active_bots: 0,
          channels_detailed: [],
          bots_detailed: [],
          recent_processed: [],
          last_updated: new Date().toISOString()
        });
      }
    } catch (error) {
      console.error('Ошибка загрузки детальной статистики AI:', error);
      // Устанавливаем fallback данные
      setDetailedStatus({
        total_channels: 0,
        total_active_bots: 0,
        channels_detailed: [],
        bots_detailed: [],
        recent_processed: [],
        last_updated: new Date().toISOString()
      });
    }
  };

  const fetchActiveTasks = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/tasks');
      const data = await response.json();
      setActiveTasks(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Ошибка загрузки активных задач:', error);
      setActiveTasks([]);
    }
  };

  const fetchChannels = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/channels');
      const data = await response.json();
      setChannels(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Ошибка загрузки каналов:', error);
      setChannels([]);
    }
  };

  const fetchOrchestratorLiveStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/orchestrator-live-status');
      if (response.ok) {
        const data = await response.json();
        setOrchestratorLiveStatus(data);
      } else {
        console.warn('Не удалось получить live статус AI Orchestrator:', response.status);
        setOrchestratorLiveStatus({
          orchestrator_active: false,
          status: 'UNAVAILABLE',
          error: `HTTP ${response.status}`
        });
      }
    } catch (error) {
      console.error('Ошибка получения live статуса AI Orchestrator:', error);
      // Устанавливаем fallback статус при ошибке
      setOrchestratorLiveStatus({
        orchestrator_active: false,
        status: 'ERROR',
        error: error.message
      });
    }
  };

  // 🆕 ФУНКЦИЯ: Получение мультитенантной статистики по ботам
  const fetchBotsWithMultitenantStats = async () => {
    console.log('🔍 Начинаем загрузку мультитенантной статистики ботов...');
    try {
      // 1. Получаем всех ботов
      console.log('📞 Запрос к /api/public-bots...');
      const botsResponse = await fetch('http://localhost:8000/api/public-bots');
      if (!botsResponse.ok) throw new Error('Failed to fetch bots');
      const allBots = await botsResponse.json();
      console.log(`✅ Получено ботов: ${allBots.length}`, allBots);
      
      // 2. Для каждого бота получаем детальную статистику
      const botsWithStatsPromises = allBots.map(async (bot) => {
        console.log(`🤖 Обрабатываем бота: ${bot.name} (ID: ${bot.id})`);
        try {
          // AI результаты для этого бота
          console.log(`   📞 Запрос AI результатов для бота ${bot.id}...`);
          const resultsResponse = await fetch(`http://localhost:8000/api/ai/results?bot_id=${bot.id}&limit=500`);
          const results = resultsResponse.ok ? await resultsResponse.json() : [];
          console.log(`   ✅ AI результатов: ${results.length}`);
          
          // Каналы бота
          console.log(`   📞 Запрос каналов для бота ${bot.id}...`);
          const channelsResponse = await fetch(`http://localhost:8000/api/public-bots/${bot.id}/channels`);
          const botChannels = channelsResponse.ok ? await channelsResponse.json() : [];
          console.log(`   ✅ Каналов: ${botChannels.length}`);
          
          // Категории бота
          console.log(`   📞 Запрос категорий для бота ${bot.id}...`);
          const categoriesResponse = await fetch(`http://localhost:8000/api/public-bots/${bot.id}/categories`);
          const botCategories = categoriesResponse.ok ? await categoriesResponse.json() : [];
          console.log(`   ✅ Категорий: ${botCategories.length}`);
          
          return {
            ...bot,
            ai_results_count: results.length,
            channels_count: botChannels.length,
            categories_count: botCategories.length,
            posts_stats: { total: 0, pending: 0, processing: 0, completed: 0, failed: 0 },
            channels: botChannels,
            categories: botCategories,
            ai_results: results.slice(0, 5)
          };
        } catch (error) {
          console.error(`❌ Ошибка получения статистики для бота ${bot.id}:`, error);
          return {
            ...bot,
            ai_results_count: 0,
            channels_count: 0,
            categories_count: 0,
            posts_stats: { total: 0, pending: 0, processing: 0, completed: 0, failed: 0 },
            channels: [],
            categories: [],
            ai_results: []
          };
        }
      });
      
      const botsWithStats = await Promise.all(botsWithStatsPromises);
      console.log('🎉 Мультитенантная статистика загружена:', botsWithStats);
      setBotsWithStats(botsWithStats);
      
    } catch (error) {
      console.error('❌ Критическая ошибка получения мультитенантной статистики ботов:', error);
      setBotsWithStats([]);
      showAlert('error', 'Ошибка загрузки статистики ботов');
    }
  };

  // 🆕 ОБРАБОТЧИК: Разворачивание/сворачивание деталей бота
  const handleBotExpand = (botId) => {
    setExpandedBot(expandedBot === botId ? null : botId);
  };

  const showAlert = (type, message) => {
    setAlert({ show: true, type, message });
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU');
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'warning';
      case 'failed': return 'error';
      case 'pending': return 'default';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon />;
      case 'processing': return <CircularProgress size={16} />;
      case 'failed': return <ErrorIcon />;
      case 'pending': return <PendingIcon />;
      default: return <PendingIcon />;
    }
  };

  // Обработчики каналов
  const handleChannelSelect = (channelId) => {
    setSelectedChannels(prev => 
      prev.includes(channelId) 
        ? prev.filter(id => id !== channelId)
        : [...prev, channelId]
    );
  };

  const handleSelectAllChannels = () => {
    if (selectedChannels.length === channels.length) {
      setSelectedChannels([]);
    } else {
      setSelectedChannels(channels.map(ch => ch.id));
    }
  };

  // Действия
  const handleReprocessAll = async () => {
    setActionLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/ai/reprocess-all', { method: 'POST' });
      const data = await response.json();
      
      if (data.success) {
        showAlert('success', `Перезапуск AI обработки инициирован. Сброшено ${data.posts_reset} постов, очищено ${data.ai_results_cleared} результатов.`);
        await loadData();
      } else {
        showAlert('error', data.message || 'Ошибка перезапуска AI обработки');
      }
    } catch (error) {
      showAlert('error', 'Ошибка выполнения операции');
    }
    setActionLoading(false);
    setConfirmDialog({ open: false, action: null, title: '', message: '' });
  };

  const handleReprocessSelectedChannels = async () => {
    if (selectedChannels.length === 0) {
      showAlert('warning', 'Выберите каналы для перезапуска');
      return;
    }

    setActionLoading(true);
    try {
      // 🚀 ИСПОЛЬЗУЕМ НОВЫЙ ENDPOINT С АВТОЗАПУСКОМ
      const response = await fetch('http://localhost:8000/api/ai/reprocess-channels-auto', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel_ids: selectedChannels })
      });
      const data = await response.json();
      
      if (data.success) {
        // Формируем сообщение с информацией об автозапуске
        let message = `Перезапуск AI обработки инициирован для ${data.channels_processed} каналов. Сброшено ${data.total_posts_reset} постов, очищено ${data.total_ai_results_cleared} результатов.`;
        
        if (data.ai_auto_start) {
          message += ` 🚀 ${data.ai_message}`;
        } else {
          message += ` ⚠️ ${data.ai_message}`;
        }
        
        showAlert('success', message);
        setSelectedChannels([]);
        await loadData();
      } else {
        showAlert('error', data.message || 'Ошибка перезапуска AI обработки для каналов');
      }
    } catch (error) {
      showAlert('error', 'Ошибка выполнения операции');
    }
    setActionLoading(false);
    setConfirmDialog({ open: false, action: null, title: '', message: '' });
  };

  const handleStopAI = async () => {
    setActionLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/ai/stop', { method: 'POST' });
      const data = await response.json();
      
      if (data.success) {
        showAlert('success', `AI обработка остановлена. ${data.posts_stopped} постов переведено в статус 'pending'.`);
        await loadData();
      } else {
        showAlert('error', data.message || 'Ошибка остановки AI обработки');
      }
    } catch (error) {
      showAlert('error', 'Ошибка выполнения операции');
    }
    setActionLoading(false);
    setConfirmDialog({ open: false, action: null, title: '', message: '' });
  };

  const handleClearResults = async () => {
    setActionLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/ai/clear-results?confirm=true', { method: 'DELETE' });
      const data = await response.json();
      
      if (data.success) {
        showAlert('success', `Удалено ${data.deleted_results} AI результатов`);
        await loadData();
      } else {
        showAlert('error', data.message || 'Ошибка очистки результатов');
      }
    } catch (error) {
      showAlert('error', 'Ошибка выполнения операции');
    }
    setActionLoading(false);
    setConfirmDialog({ open: false, action: null, title: '', message: '' });
  };

  const openConfirmDialog = (action, title, message) => {
    setConfirmDialog({ open: true, action, title, message });
  };

  const getOrchestratorStatus = () => {
    if (!orchestratorLiveStatus) {
      return { text: 'НЕИЗВЕСТНО', color: 'default', icon: '❓' };
    }

    if (orchestratorLiveStatus.orchestrator_active) {
      const status = orchestratorLiveStatus.status;
      switch (status) {
        case 'PROCESSING_STARTED':
          return { text: 'ОБРАБОТКА ЗАПУЩЕНА', color: 'info', icon: '🚀' };
        case 'PROCESSING_COMPLETED':
          return { text: 'ОБРАБОТКА ЗАВЕРШЕНА', color: 'success', icon: '✅' };
        case 'PROCESSING_FAILED':
          return { text: 'ОШИБКА ОБРАБОТКИ', color: 'error', icon: '❌' };
        case 'IDLE':
          return { text: 'ОЖИДАНИЕ', color: 'warning', icon: '⏳' };
        default:
          return { text: 'АКТИВЕН', color: 'success', icon: '🟢' };
      }
    } else {
      return { text: 'НЕ АКТИВЕН', color: 'error', icon: '🔴' };
    }
  };

  // Функция для ручного обновления данных
  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchAIStatus(),
        fetchDetailedStatus(),
        fetchActiveTasks(),
        fetchChannels(),
        fetchOrchestratorLiveStatus(),
        fetchBotsWithMultitenantStats() // 🆕 Новая функция
      ]);
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="50vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        <AssessmentIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
        Управление AI сервисами и мультитенантными данными
        
        {/* AI Orchestrator Status */}
        <Box component="span" sx={{ ml: 2 }}>
          {orchestratorLiveStatus ? (
            orchestratorLiveStatus.orchestrator_active ? (
              <Chip 
                label={`AI Orchestrator: ${getOrchestratorStatus().text}`} 
                color={getOrchestratorStatus().color} 
                icon={<span>{getOrchestratorStatus().icon}</span>}
              />
            ) : (
              <Chip label="AI Orchestrator: НЕ АКТИВЕН" color="error" />
            )
          ) : (
            <Chip label="AI Orchestrator: НЕ АКТИВЕН" color="error" />
          )}
        </Box>
      </Typography>

      <Typography variant="body2" color="text.secondary" gutterBottom>
        Обновлено: {new Date().toLocaleString('ru-RU')}
      </Typography>

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

      {/* 🎯 АККОРДЕОН С ОСНОВНЫМИ РАЗДЕЛАМИ */}
      
      {/* 🤖 РАЗДЕЛ 1: AI СЕРВИСЫ */}
      <Accordion defaultExpanded sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box display="flex" alignItems="center" gap={1}>
            <PsychologyIcon color="primary" />
            <Typography variant="h6">AI Сервисы</Typography>
            <Chip 
              label={orchestratorLiveStatus?.orchestrator_active ? 'Активен' : 'Неактивен'}
              color={orchestratorLiveStatus?.orchestrator_active ? 'success' : 'error'}
              size="small"
            />
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          
          {/* Управление AI сервисами */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <SettingsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Управление AI сервисами
              </Typography>
              
              <Grid container spacing={2}>
                {/* Основные действия */}
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Основные действия:
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<RestartAltIcon />}
                      onClick={() => openConfirmDialog(
                        handleReprocessAll,
                        'Перезапустить обработку всех постов',
                        'Это действие сбросит статус всех постов и запустит полную переобработку. Продолжить?'
                      )}
                      disabled={actionLoading}
                    >
                      Перезапустить всё
                    </Button>
                    
                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={<StopIcon />}
                      onClick={() => openConfirmDialog(
                        handleStopAI,
                        'Остановить AI обработку',
                        'Это действие остановит текущую обработку и переведет активные задачи в статус ожидания. Продолжить?'
                      )}
                      disabled={actionLoading}
                    >
                      Остановить AI
                    </Button>
                    
                    <Button
                      variant="outlined"
                      color="warning"
                      startIcon={<DeleteIcon />}
                      onClick={() => openConfirmDialog(
                        handleClearResults,
                        'Очистить результаты AI',
                        'Это действие удалит все AI результаты из базы данных. Данные нельзя будет восстановить. Продолжить?'
                      )}
                      disabled={actionLoading}
                    >
                      Очистить результаты
                    </Button>
                    
                    <Button
                      variant="outlined"
                      startIcon={<RefreshIcon />}
                      onClick={loadData}
                      disabled={loading}
                    >
                      Обновить данные
                    </Button>
                  </Stack>
                </Grid>

                {/* Статистика AI Orchestrator */}
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Статус AI Orchestrator:
                  </Typography>
                  <Box display="flex" flexDirection="column" gap={1}>
                    {orchestratorLiveStatus ? (
                      <>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Chip 
                            label={orchestratorLiveStatus.orchestrator_active ? 'Активен' : 'Неактивен'}
                            color={orchestratorLiveStatus.orchestrator_active ? 'success' : 'error'}
                            size="small"
                          />
                          <Typography variant="body2">
                            Статус: {getOrchestratorStatus().text}
                          </Typography>
                        </Box>
                        
                        {orchestratorLiveStatus.last_heartbeat && (
                          <Typography variant="caption" color="text.secondary">
                            Последний сигнал: {new Date(orchestratorLiveStatus.last_heartbeat).toLocaleString('ru-RU')}
                          </Typography>
                        )}
                        
                        {orchestratorLiveStatus.current_task && (
                          <Typography variant="caption" color="primary">
                            Текущая задача: {orchestratorLiveStatus.current_task}
                          </Typography>
                        )}
                      </>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Нет данных о статусе
                      </Typography>
                    )}
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Статистика работы AI сервисов */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <AnalyticsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Статистика работы AI сервисов
              </Typography>
              
              <Grid container spacing={3}>
                {/* Общая статистика */}
                <Grid item xs={12} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {aiStatus?.total_processed || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Всего обработано
                    </Typography>
                  </Paper>
                </Grid>
                
                <Grid item xs={12} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="warning.main">
                      {aiStatus?.total_pending || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      В очереди
                    </Typography>
                  </Paper>
                </Grid>
                
                <Grid item xs={12} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="success.main">
                      {aiStatus?.success_rate ? `${Math.round(aiStatus.success_rate * 100)}%` : 'N/A'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Успешность
                    </Typography>
                  </Paper>
                </Grid>
                
                <Grid item xs={12} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="info.main">
                      {aiStatus?.average_processing_time || 'N/A'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Среднее время
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Управление каналами для AI */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <BuildIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Управление AI обработкой по каналам
              </Typography>
              
              <Grid container spacing={2}>
                {/* Выбор каналов */}
                <Grid item xs={12} md={8}>
                  <Typography variant="subtitle2" gutterBottom>
                    Выберите каналы для перезапуска AI обработки:
                  </Typography>
                  
                  <Box display="flex" alignItems="center" gap={2} mb={2}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={selectedChannels.length === channels.length && channels.length > 0}
                          indeterminate={selectedChannels.length > 0 && selectedChannels.length < channels.length}
                          onChange={handleSelectAllChannels}
                        />
                      }
                      label="Выбрать все каналы"
                    />
                    <Typography variant="body2" color="text.secondary">
                      ({selectedChannels.length} из {channels.length} выбрано)
                    </Typography>
                  </Box>

                  <FormGroup>
                    <Grid container spacing={1}>
                      {channels.map((channel) => (
                        <Grid item xs={12} sm={6} md={4} key={channel.id}>
                          <FormControlLabel
                            control={
                              <Checkbox
                                checked={selectedChannels.includes(channel.id)}
                                onChange={() => handleChannelSelect(channel.id)}
                                size="small"
                              />
                            }
                            label={
                              <Box>
                                <Typography variant="body2" fontWeight="bold">
                                  {channel.username || channel.channel_name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {channel.telegram_id}
                                </Typography>
                              </Box>
                            }
                          />
                        </Grid>
                      ))}
                    </Grid>
                  </FormGroup>
                </Grid>

                {/* Действия с выбранными каналами */}
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2" gutterBottom>
                    Действия с выбранными каналами:
                  </Typography>
                  
                  <Stack spacing={1}>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<RestartAltIcon />}
                      onClick={() => openConfirmDialog(
                        handleReprocessSelectedChannels,
                        'Перезапустить AI обработку выбранных каналов',
                        `Это действие сбросит статус постов из ${selectedChannels.length} выбранных каналов и запустит их переобработку. Продолжить?`
                      )}
                      disabled={actionLoading || selectedChannels.length === 0}
                      fullWidth
                    >
                      Перезапустить выбранные
                    </Button>
                    
                    <Typography variant="caption" color="text.secondary" textAlign="center">
                      {selectedChannels.length === 0 
                        ? 'Выберите каналы для перезапуска' 
                        : `Будет перезапущено ${selectedChannels.length} каналов`
                      }
                    </Typography>
                  </Stack>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

        </AccordionDetails>
      </Accordion>

      {/* 🤖 РАЗДЕЛ 2: МУЛЬТИТЕНАНТНЫЕ ДАННЫЕ ПО БОТАМ */}
      <Accordion defaultExpanded sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box display="flex" alignItems="center" gap={1}>
            <SmartToyIcon color="primary" />
            <Typography variant="h6">Мультитенантные данные по ботам</Typography>
            <Chip 
              label={`${botsWithStats.length} ботов`}
              color="primary"
              size="small"
            />
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Typography>Мультитенантные данные - содержимое будет добавлено</Typography>
        </AccordionDetails>
      </Accordion>

      {/* Confirm Dialog */}
      <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({ open: false, action: null, title: '', message: '' })}>
        <DialogTitle>{confirmDialog.title}</DialogTitle>
        <DialogContent>
          <DialogContentText>{confirmDialog.message}</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ open: false, action: null, title: '', message: '' })}>
            Отмена
          </Button>
          <Button 
            onClick={confirmDialog.action} 
            color="primary" 
            disabled={actionLoading}
            startIcon={actionLoading ? <CircularProgress size={16} /> : null}
          >
            Подтвердить
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AIResultsPage; 