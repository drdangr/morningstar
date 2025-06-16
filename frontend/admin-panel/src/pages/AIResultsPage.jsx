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
  FormGroup
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
  Pause as PauseIcon
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

  useEffect(() => {
    const fetchAllData = async () => {
      setLoading(true);
      try {
        await Promise.all([
          fetchAIStatus(),
          fetchDetailedStatus(),
          fetchActiveTasks(),
          fetchChannels(),
          fetchOrchestratorLiveStatus()
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
          fetchOrchestratorLiveStatus()
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
        fetchOrchestratorLiveStatus()
      ]);
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Заголовок */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          <SmartToyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          AI Results Management
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadData}
          disabled={loading}
        >
          Обновить
        </Button>
      </Box>

      {/* Алерты */}
      {alert.show && (
        <Alert severity={alert.type} sx={{ mb: 3 }} onClose={() => setAlert({ show: false, type: 'info', message: '' })}>
          {alert.message}
        </Alert>
      )}

      {/* Панель управления каналами */}
      <Accordion sx={{ mb: 3 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">
            <TuneIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Управление AI по каналам
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            {/* Выбор каналов */}
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">Выбор каналов</Typography>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={selectedChannels.length === channels.length && channels.length > 0}
                          indeterminate={selectedChannels.length > 0 && selectedChannels.length < channels.length}
                          onChange={handleSelectAllChannels}
                        />
                      }
                      label="Выбрать все"
                    />
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
                              />
                            }
                            label={
                              <Box>
                                <Typography variant="body2" fontWeight="bold">
                                  {channel.title || channel.channel_name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {channel.username ? (channel.username.startsWith('@') ? channel.username : `@${channel.username}`) : `ID: ${channel.telegram_id}`}
                                </Typography>
                              </Box>
                            }
                          />
                        </Grid>
                      ))}
                    </Grid>
                  </FormGroup>
                  {selectedChannels.length > 0 && (
                    <Box mt={2}>
                      <Typography variant="body2" color="primary">
                        Выбрано каналов: {selectedChannels.length}
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Кнопки управления */}
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Действия</Typography>
                  <Stack spacing={2}>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<RestartAltIcon />}
                      onClick={() => openConfirmDialog(
                        handleReprocessSelectedChannels,
                        'Перезапуск AI для выбранных каналов',
                        `Вы уверены, что хотите перезапустить AI обработку для ${selectedChannels.length} выбранных каналов? Это сбросит статус всех постов этих каналов и удалит существующие AI результаты.`
                      )}
                      disabled={actionLoading || selectedChannels.length === 0}
                      fullWidth
                    >
                      Перезапустить выбранные
                    </Button>
                    
                    <Button
                      variant="contained"
                      color="warning"
                      startIcon={<StopIcon />}
                      onClick={() => openConfirmDialog(
                        handleStopAI,
                        'Остановка AI обработки',
                        'Вы уверены, что хотите остановить AI обработку? Все посты в статусе "processing" будут переведены в "pending".'
                      )}
                      disabled={actionLoading}
                      fullWidth
                    >
                      Остановить AI
                    </Button>

                    <Divider />

                    <Button
                      variant="outlined"
                      color="primary"
                      startIcon={<RestartAltIcon />}
                      onClick={() => openConfirmDialog(
                        handleReprocessAll,
                        'Полный перезапуск AI',
                        'Вы уверены, что хотите перезапустить AI обработку для ВСЕХ постов? Это сбросит статус всех постов и удалит все существующие AI результаты.'
                      )}
                      disabled={actionLoading}
                      fullWidth
                    >
                      Перезапустить все
                    </Button>

                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={<DeleteIcon />}
                      onClick={() => openConfirmDialog(
                        handleClearResults,
                        'Очистка AI результатов',
                        'Вы уверены, что хотите удалить ВСЕ AI результаты? Статус постов не изменится, но все AI анализы будут потеряны.'
                      )}
                      disabled={actionLoading}
                      fullWidth
                    >
                      Очистить результаты
                    </Button>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Статистика */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Статистика постов */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Статистика постов
              </Typography>
              {aiStatus?.posts_stats && (
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Всего постов: {aiStatus.posts_stats.total}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={aiStatus.posts_stats.total > 0 ? Math.round((aiStatus.posts_stats.completed / aiStatus.posts_stats.total) * 100) : 0}
                      sx={{ mt: 1 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      Обработано: {aiStatus.posts_stats.total > 0 ? Math.round((aiStatus.posts_stats.completed / aiStatus.posts_stats.total) * 100) : 0}%
                    </Typography>
                  </Box>
                  <Divider />
                  <Grid container spacing={1}>
                    <Grid item xs={6}>
                      <Chip
                        label={`Ожидают: ${aiStatus.posts_stats.pending}`}
                        color="default"
                        size="small"
                        icon={<PendingIcon />}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <Chip
                        label={`Обработка: ${aiStatus.posts_stats.processing}`}
                        color="warning"
                        size="small"
                        icon={<CircularProgress size={16} />}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <Chip
                        label={`Готово: ${aiStatus.posts_stats.completed}`}
                        color="success"
                        size="small"
                        icon={<CheckCircleIcon />}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <Chip
                        label={`Ошибки: ${aiStatus.posts_stats.failed}`}
                        color="error"
                        size="small"
                        icon={<ErrorIcon />}
                      />
                    </Grid>
                  </Grid>
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Статистика AI результатов */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <PsychologyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                AI Результаты
              </Typography>
              {aiStatus?.ai_results_stats && (
                <Stack spacing={2}>
                  <Typography variant="h4" color="primary">
                    {aiStatus.ai_results_stats.total_results}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Всего AI результатов
                  </Typography>
                  <Divider />
                  <Typography variant="body2">
                    Результатов на пост: {aiStatus.ai_results_stats.results_per_post}
                  </Typography>
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Статистика ботов */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <SmartToyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Активные боты
              </Typography>
              {aiStatus?.bots_stats && (
                <Stack spacing={2}>
                  <Typography variant="h4" color="primary">
                    {aiStatus.bots_stats.total_processing_bots}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Ботов в обработке
                  </Typography>
                  <Divider />
                  <Grid container spacing={1}>
                    <Grid item xs={6}>
                      <Chip
                        label={`Активные: ${aiStatus.bots_stats.active_bots}`}
                        color="success"
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <Chip
                        label={`Разработка: ${aiStatus.bots_stats.development_bots}`}
                        color="info"
                        size="small"
                      />
                    </Grid>
                  </Grid>
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 🚀 РАСШИРЕННАЯ ДЕТАЛЬНАЯ СТАТИСТИКА AI СЕРВИСОВ */}
      {detailedStatus && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                <AnalyticsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Детальная статистика AI сервисов
              </Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <Chip
                  label={`AI Orchestrator: ${getOrchestratorStatus().text}`}
                  color={getOrchestratorStatus().color}
                  icon={<span>{getOrchestratorStatus().icon}</span>}
                />
                {orchestratorLiveStatus && orchestratorLiveStatus.orchestrator_active && (
                  <Tooltip title={`Детали: ${JSON.stringify(orchestratorLiveStatus.details, null, 2)}`}>
                    <Chip
                      label={`Последнее обновление: ${orchestratorLiveStatus.time_since_update}с назад`}
                      size="small"
                      variant="outlined"
                    />
                  </Tooltip>
                )}
                {orchestratorLiveStatus && orchestratorLiveStatus.stats && (
                  <Tooltip title={`Статистика: Обработано ${orchestratorLiveStatus.stats.total_processed || 0}, Успешно ${orchestratorLiveStatus.stats.successful_processed || 0}`}>
                    <Chip
                      label={`Статистика AI`}
                      size="small"
                      variant="outlined"
                      color="info"
                    />
                  </Tooltip>
                )}
                <Typography variant="caption" color="text.secondary">
                  Обновлено: {formatDate(detailedStatus.last_updated)}
                </Typography>
              </Box>
            </Box>

            <Tabs value={detailedTabValue} onChange={(e, newValue) => setDetailedTabValue(newValue)} sx={{ mb: 2 }}>
              <Tab label={`Каналы (${detailedStatus.total_channels})`} />
              <Tab label={`Боты (${detailedStatus.total_active_bots})`} />
              <Tab label="Последние обработанные" />
            </Tabs>

            <TabPanel value={detailedTabValue} index={0}>
              {/* Статистика по каналам */}
              {detailedStatus.channels_detailed && detailedStatus.channels_detailed.length > 0 ? (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Канал</TableCell>
                        <TableCell align="center">Всего постов</TableCell>
                        <TableCell align="center">Ожидают</TableCell>
                        <TableCell align="center">Обработка</TableCell>
                        <TableCell align="center">Готово</TableCell>
                        <TableCell align="center">Ошибки</TableCell>
                        <TableCell align="center">Прогресс</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {detailedStatus.channels_detailed.map((channel) => (
                        <TableRow key={channel.telegram_id}>
                          <TableCell>
                            <Box>
                              <Typography variant="body2" fontWeight="bold">
                                {channel.name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {channel.username ? (channel.username.startsWith('@') ? channel.username : `@${channel.username}`) : `ID: ${channel.telegram_id}`}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="center">
                            <Typography variant="body2" fontWeight="bold">
                              {channel.total_posts}
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <Chip label={channel.pending} color="default" size="small" />
                          </TableCell>
                          <TableCell align="center">
                            <Chip 
                              label={channel.processing} 
                              color={channel.processing > 0 ? "warning" : "default"} 
                              size="small" 
                            />
                          </TableCell>
                          <TableCell align="center">
                            <Chip label={channel.completed} color="success" size="small" />
                          </TableCell>
                          <TableCell align="center">
                            <Chip 
                              label={channel.failed} 
                              color={channel.failed > 0 ? "error" : "default"} 
                              size="small" 
                            />
                          </TableCell>
                          <TableCell align="center">
                            <Box display="flex" alignItems="center" gap={1}>
                              <LinearProgress 
                                variant="determinate" 
                                value={channel.progress || 0} 
                                sx={{ width: 60, height: 6 }}
                                color={channel.progress === 100 ? "success" : "primary"}
                              />
                              <Typography variant="caption">
                                {channel.progress || 0}%
                              </Typography>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography variant="body2" color="text.secondary" textAlign="center" py={2}>
                  Нет данных по каналам
                </Typography>
              )}
            </TabPanel>

            <TabPanel value={detailedTabValue} index={1}>
              {/* Статистика по ботам */}
              {detailedStatus.bots_detailed && detailedStatus.bots_detailed.length > 0 ? (
                <Grid container spacing={2}>
                  {detailedStatus.bots_detailed.map((bot) => (
                    <Grid item xs={12} md={6} key={bot.bot_id}>
                      <Card variant="outlined">
                        <CardContent>
                          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                            <Typography variant="h6" noWrap>
                              {bot.name}
                            </Typography>
                            <Chip 
                              label={bot.status} 
                              color={bot.status === 'active' ? 'success' : 'info'} 
                              size="small" 
                            />
                          </Box>
                          <Typography variant="h4" color="primary" gutterBottom>
                            {bot.results_count}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            AI результатов обработано
                          </Typography>
                          {bot.last_processed && (
                            <Typography variant="caption" color="text.secondary">
                              Последняя обработка: {formatDate(bot.last_processed)}
                            </Typography>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Typography variant="body2" color="text.secondary" textAlign="center" py={2}>
                  Нет данных по ботам
                </Typography>
              )}
            </TabPanel>

            <TabPanel value={detailedTabValue} index={2}>
              {/* Последние обработанные посты */}
              {detailedStatus.recent_processed && detailedStatus.recent_processed.length > 0 ? (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Пост ID</TableCell>
                        <TableCell>Бот</TableCell>
                        <TableCell>Канал</TableCell>
                        <TableCell>Содержание</TableCell>
                        <TableCell>Обработано</TableCell>
                        <TableCell>Версия</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {detailedStatus.recent_processed.map((item, index) => (
                        <TableRow key={`${item.post_id}-${item.bot_id}-${index}`}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="bold">
                              {item.post_id}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {item.bot_name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {item.channel_name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                              {item.content_preview}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption">
                              {formatDate(item.processed_at)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip label={item.processing_version} size="small" />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography variant="body2" color="text.secondary" textAlign="center" py={2}>
                  Нет недавно обработанных постов
                </Typography>
              )}
            </TabPanel>
          </CardContent>
        </Card>
      )}

      {/* Активные AI задачи */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <PendingIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Активные AI задачи ({activeTasks.length})
          </Typography>
          
          {activeTasks.length === 0 ? (
            <Box textAlign="center" py={4}>
              <Typography variant="body1" color="text.secondary">
                Нет активных AI задач
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Все посты обработаны или ожидают запуска обработки
              </Typography>
            </Box>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>ID поста</TableCell>
                    <TableCell>Канал</TableCell>
                    <TableCell>Содержание</TableCell>
                    <TableCell>Статус</TableCell>
                    <TableCell>Дата</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {activeTasks.map((task) => (
                    <TableRow key={task.post_id}>
                      <TableCell>{task.post_id}</TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight="bold">
                          {task.channel_name || 'Неизвестно'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          ID: {task.channel_telegram_id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                          {task.content ? task.content.substring(0, 100) + '...' : 'Нет содержания'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={task.processing_status}
                          color={getStatusColor(task.processing_status)}
                          size="small"
                          icon={getStatusIcon(task.processing_status)}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption">
                          {formatDate(task.collected_at)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Диалог подтверждения */}
      <Dialog
        open={confirmDialog.open}
        onClose={() => setConfirmDialog({ open: false, action: null, title: '', message: '' })}
      >
        <DialogTitle>{confirmDialog.title}</DialogTitle>
        <DialogContent>
          <DialogContentText>{confirmDialog.message}</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setConfirmDialog({ open: false, action: null, title: '', message: '' })}
            disabled={actionLoading}
          >
            Отмена
          </Button>
          <Button 
            onClick={confirmDialog.action} 
            variant="contained" 
            disabled={actionLoading}
            startIcon={actionLoading ? <CircularProgress size={16} /> : null}
          >
            {actionLoading ? 'Выполняется...' : 'Подтвердить'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AIResultsPage; 