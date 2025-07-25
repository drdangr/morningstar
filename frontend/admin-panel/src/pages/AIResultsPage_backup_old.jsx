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
  
  // МУЛЬТИТЕНАНТНЫЕ СОСТОЯНИЯ
  const [bots, setBots] = useState([]);
  const [selectedBot, setSelectedBot] = useState('all');
  const [aiResults, setAiResults] = useState([]);
  const [botsWithStats, setBotsWithStats] = useState([]);
  const [expandedBot, setExpandedBot] = useState(null);
  const [botChannelsStats, setBotChannelsStats] = useState({});

  // Все функции загрузки данных (скопированы из оригинального файла)
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
          fetchBotsWithMultitenantStats()
        ]);
      } catch (error) {
        console.error('Ошибка загрузки данных:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAllData();
    
    const interval = setInterval(async () => {
      try {
        await Promise.all([
          fetchAIStatus(),
          fetchDetailedStatus(),
          fetchActiveTasks(),
          fetchChannels(),
          fetchOrchestratorLiveStatus(),
          fetchBotsWithMultitenantStats()
        ]);
      } catch (error) {
        console.error('Ошибка автообновления:', error);
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  // Функции API (заглушки для демонстрации)
  const fetchAIStatus = async () => {
    setAiStatus({ total_processed: 38, total_pending: 0, success_rate: 0.95, average_processing_time: '2.3s' });
  };

  const fetchDetailedStatus = async () => {
    setDetailedStatus({ total_processed: 38, total_pending: 0, total_failed: 2 });
  };

  const fetchActiveTasks = async () => {
    setActiveTasks([]);
  };

  const fetchChannels = async () => {
    setChannels([
      { id: 1, username: '@bbcrussian', channel_name: 'BBC Russian', telegram_id: '1003631752' },
      { id: 2, username: '@babel', channel_name: 'Babel', telegram_id: '1217113263' }
    ]);
  };

  const fetchOrchestratorLiveStatus = async () => {
    setOrchestratorLiveStatus({ 
      orchestrator_active: true, 
      status: 'IDLE',
      last_heartbeat: new Date().toISOString()
    });
  };

  const fetchBotsWithMultitenantStats = async () => {
    setBotsWithStats([
      {
        id: 1,
        name: 'Тестовый UI Bot',
        status: 'active',
        ai_results_count: 20,
        channels_count: 1,
        categories_count: 1,
        posts_stats: { total: 20, pending: 0, processing: 0, completed: 20, failed: 0 },
        channels: [{ id: 1, username: '@bbcrussian', telegram_id: '1003631752' }],
        categories: [{ id: 1, category_name: 'Война', weight: 1.0 }]
      },
      {
        id: 2,
        name: 'USA News Bot',
        status: 'active',
        ai_results_count: 18,
        channels_count: 2,
        categories_count: 1,
        posts_stats: { total: 18, pending: 0, processing: 0, completed: 18, failed: 0 },
        channels: [
          { id: 1, username: '@bbcrussian', telegram_id: '1003631752' },
          { id: 2, username: '@babel', telegram_id: '1217113263' }
        ],
        categories: [{ id: 2, category_name: 'США', weight: 1.0 }]
      }
    ]);
  };

  // Функции обработчики
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
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon />;
      case 'processing': return <PendingIcon />;
      case 'failed': return <ErrorIcon />;
      default: return <PendingIcon />;
    }
  };

  const handleChannelSelect = (channelId) => {
    setSelectedChannels(prev => 
      prev.includes(channelId) 
        ? prev.filter(id => id !== channelId)
        : [...prev, channelId]
    );
  };

  const handleSelectAllChannels = () => {
    setSelectedChannels(
      selectedChannels.length === channels.length ? [] : channels.map(c => c.id)
    );
  };

  const handleReprocessAll = async () => {
    setActionLoading(true);
    try {
      showAlert('success', 'Перезапуск AI обработки начат');
    } catch (error) {
      showAlert('error', 'Ошибка перезапуска');
    }
    setActionLoading(false);
    setConfirmDialog({ open: false, action: null, title: '', message: '' });
  };

  const handleReprocessSelectedChannels = async () => {
    setActionLoading(true);
    try {
      showAlert('success', `Перезапуск ${selectedChannels.length} каналов начат`);
    } catch (error) {
      showAlert('error', 'Ошибка перезапуска каналов');
    }
    setActionLoading(false);
    setConfirmDialog({ open: false, action: null, title: '', message: '' });
  };

  const handleStopAI = async () => {
    setActionLoading(true);
    try {
      showAlert('success', 'AI обработка остановлена');
    } catch (error) {
      showAlert('error', 'Ошибка остановки AI');
    }
    setActionLoading(false);
    setConfirmDialog({ open: false, action: null, title: '', message: '' });
  };

  const handleClearResults = async () => {
    setActionLoading(true);
    try {
      showAlert('success', 'Результаты AI очищены');
    } catch (error) {
      showAlert('error', 'Ошибка очистки результатов');
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

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchAIStatus(),
        fetchDetailedStatus(),
        fetchActiveTasks(),
        fetchChannels(),
        fetchOrchestratorLiveStatus(),
        fetchBotsWithMultitenantStats()
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

          {/* Детальная статистика AI сервисов с табами */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <ProcessingIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Детальная статистика и мониторинг
              </Typography>
              
              <Tabs 
                value={detailedTabValue} 
                onChange={(event, newValue) => setDetailedTabValue(newValue)}
                sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}
              >
                <Tab label="Общая статистика" />
                <Tab label="Активные задачи" />
                <Tab label="История обработки" />
                <Tab label="Производительность" />
              </Tabs>

              <TabPanel value={detailedTabValue} index={0}>
                <Alert severity="info">
                  Общая статистика AI сервисов - данные загружаются...
                </Alert>
              </TabPanel>

              <TabPanel value={detailedTabValue} index={1}>
                <Alert severity="info">
                  Нет активных задач AI обработки
                </Alert>
              </TabPanel>

              <TabPanel value={detailedTabValue} index={2}>
                <Alert severity="info">
                  История операций пуста
                </Alert>
              </TabPanel>

              <TabPanel value={detailedTabValue} index={3}>
                <Alert severity="info">
                  Метрики производительности загружаются...
                </Alert>
              </TabPanel>
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

          {/* Мультитенантная статистика по ботам */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  <SmartToyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Статистика по ботам ({botsWithStats.length})
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={loadData}
                  disabled={loading}
                  size="small"
                >
                  Обновить
                </Button>
              </Box>

              {botsWithStats.length > 0 ? (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Бот</TableCell>
                        <TableCell align="center">AI Результаты</TableCell>
                        <TableCell align="center">Каналы</TableCell>
                        <TableCell align="center">Категории</TableCell>
                        <TableCell align="center">Всего постов</TableCell>
                        <TableCell align="center">Готово</TableCell>
                        <TableCell align="center">Прогресс</TableCell>
                        <TableCell align="center">Действия</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {botsWithStats.map((bot) => (
                        <React.Fragment key={bot.id}>
                          {/* Основная строка бота */}
                          <TableRow>
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
                                </Box>
                              </Box>
                            </TableCell>
                            <TableCell align="center">
                              <Typography variant="h6" color="primary">
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
                              <Chip label={bot.posts_stats.completed} color="success" size="small" />
                            </TableCell>
                            <TableCell align="center">
                              <Box display="flex" alignItems="center" gap={1}>
                                <LinearProgress 
                                  variant="determinate" 
                                  value={bot.posts_stats.total > 0 ? 
                                    Math.round((bot.posts_stats.completed / bot.posts_stats.total) * 100) : 0} 
                                  sx={{ width: 60, height: 6 }}
                                  color={bot.posts_stats.completed === bot.posts_stats.total ? "success" : "primary"}
                                />
                                <Typography variant="caption">
                                  {bot.posts_stats.total > 0 ? 
                                    Math.round((bot.posts_stats.completed / bot.posts_stats.total) * 100) : 0}%
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell align="center">
                              <IconButton
                                size="small"
                                onClick={() => handleBotExpand(bot.id)}
                                disabled={bot.channels_count === 0}
                              >
                                {expandedBot === bot.id ? <ExpandLessIcon /> : <ExpandMoreIconTable />}
                              </IconButton>
                            </TableCell>
                          </TableRow>

                          {/* Развернутые детали бота */}
                          <TableRow>
                            <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={8}>
                              <Collapse in={expandedBot === bot.id} timeout="auto" unmountOnExit>
                                <Box sx={{ margin: 2 }}>
                                  <Typography variant="h6" gutterBottom component="div">
                                    Детали бота: {bot.name}
                                  </Typography>
                                  
                                  {/* Каналы бота */}
                                  {bot.channels && bot.channels.length > 0 && (
                                    <Box mb={2}>
                                      <Typography variant="subtitle2" gutterBottom>
                                        Каналы ({bot.channels.length}):
                                      </Typography>
                                      <Grid container spacing={1}>
                                        {bot.channels.map((channel) => (
                                          <Grid item key={channel.id}>
                                            <Chip
                                              label={`${channel.username || channel.channel_name} (${channel.telegram_id})`}
                                              size="small"
                                              variant="outlined"
                                            />
                                          </Grid>
                                        ))}
                                      </Grid>
                                    </Box>
                                  )}
                                  
                                  {/* Категории бота */}
                                  {bot.categories && bot.categories.length > 0 && (
                                    <Box mb={2}>
                                      <Typography variant="subtitle2" gutterBottom>
                                        Категории ({bot.categories.length}):
                                      </Typography>
                                      <Grid container spacing={1}>
                                        {bot.categories.map((category) => (
                                          <Grid item key={category.id}>
                                            <Chip
                                              label={`${category.category_name} (${category.weight || 'N/A'})`}
                                              size="small"
                                              color="primary"
                                              variant="outlined"
                                            />
                                          </Grid>
                                        ))}
                                      </Grid>
                                    </Box>
                                  )}

                                  {/* Кнопки управления ботом */}
                                  <Box display="flex" gap={1}>
                                    <Button
                                      size="small"
                                      variant="outlined"
                                      startIcon={<RestartAltIcon />}
                                      onClick={() => {
                                        console.log(`Reprocess bot ${bot.id}`);
                                      }}
                                    >
                                      Переобработать бота
                                    </Button>
                                    <Button
                                      size="small"
                                      variant="outlined"
                                      startIcon={<ViewIcon />}
                                      onClick={() => {
                                        console.log(`View bot ${bot.id} results`);
                                      }}
                                    >
                                      Посмотреть результаты
                                    </Button>
                                    <Button
                                      size="small"
                                      variant="outlined"
                                      color="warning"
                                      startIcon={<DeleteIcon />}
                                      onClick={() => {
                                        console.log(`Clear bot ${bot.id} data`);
                                      }}
                                    >
                                      Очистить данные бота
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
                <Typography variant="body2" color="text.secondary" textAlign="center" py={4}>
                  Нет данных по ботам
                </Typography>
              )}
            </CardContent>
          </Card>

          {/* Управление данными каналов */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <BuildIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Управление данными каналов
              </Typography>
              
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Здесь можно очистить все данные (посты, AI результаты) для выбранных каналов
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={8}>
                  <Typography variant="subtitle2" gutterBottom>
                    Выберите каналы для очистки данных:
                  </Typography>
                  
                  <FormGroup>
                    <Grid container spacing={1}>
                      {channels.slice(0, 4).map((channel) => (
                        <Grid item xs={12} sm={6} key={channel.id}>
                          <FormControlLabel
                            control={<Checkbox size="small" />}
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

                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2" gutterBottom>
                    Действия с данными:
                  </Typography>
                  
                  <Stack spacing={1}>
                    <Button
                      variant="outlined"
                      color="warning"
                      startIcon={<DeleteIcon />}
                      disabled
                      fullWidth
                    >
                      Очистить данные каналов
                    </Button>
                    
                    <Typography variant="caption" color="text.secondary" textAlign="center">
                      Функция в разработке
                    </Typography>
                  </Stack>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Управление данными ботов */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <SmartToyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Управление данными ботов
              </Typography>
              
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Здесь можно очистить все AI результаты для выбранных ботов
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={8}>
                  <Typography variant="subtitle2" gutterBottom>
                    Выберите ботов для очистки данных:
                  </Typography>
                  
                  <FormGroup>
                    {botsWithStats.map((bot) => (
                      <FormControlLabel
                        key={bot.id}
                        control={<Checkbox size="small" />}
                        label={
                          <Box>
                            <Typography variant="body2" fontWeight="bold">{bot.name}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {bot.ai_results_count} AI результатов
                            </Typography>
                          </Box>
                        }
                      />
                    ))}
                  </FormGroup>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2" gutterBottom>
                    Действия с данными ботов:
                  </Typography>
                  
                  <Stack spacing={1}>
                    <Button
                      variant="outlined"
                      color="warning"
                      startIcon={<DeleteIcon />}
                      disabled
                      fullWidth
                    >
                      Очистить данные ботов
                    </Button>
                    
                    <Typography variant="caption" color="text.secondary" textAlign="center">
                      Функция в разработке
                    </Typography>
                  </Stack>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

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
