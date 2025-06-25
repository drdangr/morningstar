import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Grid, Card, CardContent, Chip, Alert, CircularProgress,
  Tab, Tabs, Button, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions,
  Rating, List, ListItem, IconButton, Accordion, AccordionSummary, AccordionDetails,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Stack,
  LinearProgress, Checkbox, FormControlLabel, FormGroup, Snackbar, Collapse
} from '@mui/material';

import {
  SmartToy as SmartToyIcon, Analytics as AnalyticsIcon, Speed as ProcessingIcon,
  ExpandMore as ExpandMoreIcon, Visibility as ViewIcon, Refresh as RefreshIcon,
  Stop as StopIcon, Delete as DeleteIcon, Assessment as AssessmentIcon,
  Psychology as PsychologyIcon, CheckCircle as CheckCircleIcon, Error as ErrorIcon,
  Pending as PendingIcon, RestartAlt as RestartAltIcon, ExpandLess as ExpandLessIcon,
  ExpandMore as ExpandMoreIconTable, Settings as SettingsIcon, Build as BuildIcon,
  Memory as MemoryIcon, Timeline as TimelineIcon, Dashboard as DashboardIcon,
  PlayArrow as PlayArrowIcon, Pause as PauseIcon, Computer as ComputerIcon,
  ViewList as ViewListIcon, MonitorHeart as MonitorHeartIcon
} from '@mui/icons-material';

import DataCleanup from '../components/DataCleanup';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const AIResultsPage = () => {
  // Основные состояния
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [alert, setAlert] = useState({ show: false, type: 'info', message: '' });
  const [confirmDialog, setConfirmDialog] = useState({ open: false, action: null, title: '', message: '' });
  
  // AI Orchestrator состояния
  const [orchestratorStatus, setOrchestratorStatus] = useState(null);
  const [aiServicesStats, setAiServicesStats] = useState(null);
  const [activeTasks, setActiveTasks] = useState([]);
  const [detailedTabValue, setDetailedTabValue] = useState(0);
  
  // Новые состояния для детальной статистики
  const [detailedAIStatus, setDetailedAIStatus] = useState(null);
  const [orchestratorCommands, setOrchestratorCommands] = useState([]);
  const [recentProcessedPosts, setRecentProcessedPosts] = useState([]);
  const [channelsDetailedStats, setChannelsDetailedStats] = useState([]);
  const [botsDetailedStats, setBotsDetailedStats] = useState([]);
  
  // Мультитенантные состояния
  const [botsWithStats, setBotsWithStats] = useState([]);
  const [multitenantStats, setMultitenantStats] = useState(null);
  const [channels, setChannels] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);
  const [selectedBots, setSelectedBots] = useState([]);
  const [expandedBot, setExpandedBot] = useState(null);
  
  // Состояния для фонового управления AI Orchestrator
  const [backgroundProcessStatus, setBackgroundProcessStatus] = useState(null);
  const [orchestratorLogs, setOrchestratorLogs] = useState([]);
  const [showLogs, setShowLogs] = useState(false);

  // Загрузка данных при монтировании
  useEffect(() => {
    loadAllData();
    const interval = setInterval(loadAllData, 8000); // Чаще обновляем для детальной статистики
    return () => clearInterval(interval);
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchOrchestratorStatus(),
        fetchAIServicesStats(),
        fetchActiveTasks(),
        fetchDetailedAIStatus(),
        fetchOrchestratorCommands(),
        fetchBotsWithStats(),
        fetchMultitenantStats(),
        fetchChannels(),
        fetchOrchestratorLogs()
      ]);
    } catch (error) {
      showAlert('error', 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  // Новые функции для детальной статистики AI Orchestrator
  const fetchDetailedAIStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/detailed-status');
      if (response.ok) {
        const data = await response.json();
        setDetailedAIStatus(data);
        setChannelsDetailedStats(data.channels_detailed || []);
        setBotsDetailedStats(data.bots_detailed || []);
        setRecentProcessedPosts(data.recent_processed || []);
      }
    } catch (error) {
      console.error('Ошибка загрузки детальной статистики AI:', error);
    }
  };

  const fetchOrchestratorCommands = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/orchestrator-commands');
      if (response.ok) {
        const data = await response.json();
        setOrchestratorCommands(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      setOrchestratorCommands([]);
    }
  };

  // Обновляем loadAllData для включения новых функций
  const loadAllDataEnhanced = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchOrchestratorStatus(),
        fetchAIServicesStats(),
        fetchActiveTasks(),
        fetchDetailedAIStatus(),
        fetchOrchestratorCommands(),
        fetchBotsWithStats(),
        fetchChannels()
      ]);
    } catch (error) {
      showAlert('error', 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  // API функции
  const fetchOrchestratorStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/orchestrator-live-status');
      const data = response.ok ? await response.json() : 
        { orchestrator_active: false, status: 'UNAVAILABLE' };
      setOrchestratorStatus(data);
      
      // Обновляем статус фонового процесса из расширенной диагностики
      if (data.background_control) {
        setBackgroundProcessStatus(data.background_control);
      }
    } catch (error) {
      setOrchestratorStatus({ orchestrator_active: false, status: 'ERROR', error: error.message });
      setBackgroundProcessStatus({ is_running: false, process_id: null });
    }
  };

  const fetchAIServicesStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/status');
      if (response.ok) {
        const data = await response.json();
        setAiServicesStats(data);
        console.log('🚀 Мультитенантная статистика AI:', data.multitenant_stats);
      }
    } catch (error) {
      console.error('Ошибка загрузки статистики AI:', error);
    }
  };

  const fetchActiveTasks = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/tasks');
      setActiveTasks(response.ok ? await response.json() : []);
    } catch (error) {
      setActiveTasks([]);
    }
  };

  const fetchBotsWithStats = async () => {
    try {
      const botsResponse = await fetch('http://localhost:8000/api/public-bots');
      if (!botsResponse.ok) throw new Error('Failed to fetch bots');
      const allBots = await botsResponse.json();
      
      const botsWithStatsPromises = allBots.map(async (bot) => {
        try {
          const [resultsResponse, channelsResponse, categoriesResponse] = await Promise.all([
            fetch(`http://localhost:8000/api/ai/results?bot_id=${bot.id}&limit=500`),
            fetch(`http://localhost:8000/api/public-bots/${bot.id}/channels`),
            fetch(`http://localhost:8000/api/public-bots/${bot.id}/categories`)
          ]);
          
          const results = resultsResponse.ok ? await resultsResponse.json() : [];
          const botChannels = channelsResponse.ok ? await channelsResponse.json() : [];
          const botCategories = categoriesResponse.ok ? await categoriesResponse.json() : [];
          
          return {
            ...bot,
            ai_results_count: results.length,
            channels_count: botChannels.length,
            categories_count: botCategories.length,
            channels: botChannels,
            categories: botCategories,
            posts_stats: { total: results.length, completed: results.length, pending: 0, failed: 0 }
          };
        } catch (error) {
          return {
            ...bot, ai_results_count: 0, channels_count: 0, categories_count: 0,
            channels: [], categories: [], posts_stats: { total: 0, completed: 0, pending: 0, failed: 0 }
          };
        }
      });
      
      setBotsWithStats(await Promise.all(botsWithStatsPromises));
    } catch (error) {
      setBotsWithStats([]);
    }
  };

  // Новые API функции для управления фоновым процессом
  const fetchOrchestratorLogs = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/orchestrator/logs?limit=50');
      if (response.ok) {
        const data = await response.json();
        setOrchestratorLogs(data.logs || []);
      }
    } catch (error) {
      console.error('Ошибка загрузки логов:', error);
      setOrchestratorLogs([]);
    }
  };

  const startBackgroundProcess = async () => {
    setActionLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/ai/orchestrator/start-background', {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        showAlert('success', data.message);
        setBackgroundProcessStatus({ is_running: true, process_id: data.process_id });
        await fetchOrchestratorLogs(); // Обновляем логи
      } else {
        showAlert('error', data.message);
      }
    } catch (error) {
      showAlert('error', 'Ошибка запуска фонового процесса');
    } finally {
      setActionLoading(false);
    }
  };

  const stopBackgroundProcess = async () => {
    setActionLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/ai/orchestrator/stop-background', {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        showAlert('success', data.message);
        setBackgroundProcessStatus({ is_running: false, process_id: null });
        await fetchOrchestratorLogs(); // Обновляем логи
      } else {
        showAlert('error', data.message);
      }
    } catch (error) {
      showAlert('error', 'Ошибка остановки фонового процесса');
    } finally {
      setActionLoading(false);
    }
  };

  const restartOrchestratorProcess = async () => {
    setActionLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/ai/orchestrator/restart', {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        showAlert('success', data.message);
        setBackgroundProcessStatus({ is_running: true, process_id: data.start_result?.process_id });
        await fetchOrchestratorLogs(); // Обновляем логи
      } else {
        showAlert('error', data.message);
      }
    } catch (error) {
      showAlert('error', 'Ошибка перезапуска процесса');
    } finally {
      setActionLoading(false);
    }
  };

  const fetchMultitenantStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/multitenant-status');
      if (response.ok) {
        const data = await response.json();
        setMultitenantStats(data);
        console.log('🚀 Полная мультитенантная статистика:', data);
      }
    } catch (error) {
      console.error('Ошибка загрузки мультитенантной статистики:', error);
    }
  };

  const fetchChannels = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/channels');
      setChannels(response.ok ? await response.json() : []);
    } catch (error) {
      setChannels([]);
    }
  };

  // Обработчики
  const showAlert = (type, message) => setAlert({ show: true, type, message });
  const openConfirmDialog = (action, title, message) => setConfirmDialog({ open: true, action, title, message });

  const handleRestartAll = async () => {
    setActionLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/ai/reprocess-all', { method: 'POST' });
      const data = await response.json();
      showAlert(data.success ? 'success' : 'error', 
        data.success ? `Перезапуск инициирован. Сброшено ${data.posts_reset} постов.` : 
        data.message || 'Ошибка перезапуска');
      if (data.success) await loadAllData();
    } catch (error) {
      showAlert('error', 'Ошибка выполнения операции');
    }
    setActionLoading(false);
    setConfirmDialog({ open: false, action: null, title: '', message: '' });
  };

  const handleBotExpand = (botId) => setExpandedBot(expandedBot === botId ? null : botId);
  
  const handleChannelSelect = (channelId) => {
    setSelectedChannels(prev => 
      prev.includes(channelId) ? prev.filter(id => id !== channelId) : [...prev, channelId]
    );
  };

  const getOrchestratorStatusInfo = () => {
    if (!orchestratorStatus) return { text: 'НЕИЗВЕСТНО', color: 'default', icon: '❓' };
    if (orchestratorStatus.orchestrator_active) {
      switch (orchestratorStatus.status) {
        case 'PROCESSING_STARTED': return { text: 'ОБРАБОТКА ЗАПУЩЕНА', color: 'info', icon: '🚀' };
        case 'PROCESSING_COMPLETED': return { text: 'ОБРАБОТКА ЗАВЕРШЕНА', color: 'success', icon: '✅' };
        case 'PROCESSING_FAILED': return { text: 'ОШИБКА ОБРАБОТКИ', color: 'error', icon: '❌' };
        case 'IDLE': return { text: 'ОЖИДАНИЕ', color: 'warning', icon: '⏳' };
        default: return { text: 'АКТИВЕН', color: 'success', icon: '🟢' };
      }
    }
    return { text: 'НЕ АКТИВЕН', color: 'error', icon: '🔴' };
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        <AssessmentIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
        Управление AI системой и мультитенантными данными
        <Box component="span" sx={{ ml: 2 }}>
          <Chip 
            label={orchestratorStatus?.orchestrator_active ? 'AI Активен' : 'AI Неактивен'}
            color={orchestratorStatus?.orchestrator_active ? 'success' : 'error'}
            icon={<span>{orchestratorStatus?.orchestrator_active ? '🟢' : '🔴'}</span>}
          />
        </Box>
      </Typography>

      <Typography variant="body2" color="text.secondary" gutterBottom>
        Последнее обновление: {new Date().toLocaleString('ru-RU')}
      </Typography>

      {/* Alert Snackbar */}
      <Snackbar open={alert.show} autoHideDuration={6000} 
        onClose={() => setAlert({ show: false, type: 'info', message: '' })}>
        <Alert severity={alert.type} onClose={() => setAlert({ show: false, type: 'info', message: '' })}>
          {alert.message}
        </Alert>
      </Snackbar>

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
          <Button onClick={confirmDialog.action} variant="contained" disabled={actionLoading}>
            {actionLoading ? <CircularProgress size={20} /> : 'Продолжить'}
          </Button>
        </DialogActions>
      </Dialog>

      {loading && (
        <Box display="flex" justifyContent="center" my={2}>
          <CircularProgress />
        </Box>
      )}

      {/* РАЗДЕЛ 1: AI ORCHESTRATOR */}
      <Accordion defaultExpanded sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box display="flex" alignItems="center" gap={1}>
            <PsychologyIcon color="primary" />
            <Typography variant="h6">AI Orchestrator и сервисы</Typography>
            <Chip 
              label={orchestratorStatus?.orchestrator_active ? 'Активен' : 'Неактивен'}
              color={orchestratorStatus?.orchestrator_active ? 'success' : 'error'}
              size="small"
            />
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          {/* Управление AI Orchestrator */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <SettingsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Управление AI Orchestrator
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>Статус AI Orchestrator:</Typography>
                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <Chip 
                      label={getOrchestratorStatusInfo().text}
                      color={getOrchestratorStatusInfo().color}
                      icon={<span>{getOrchestratorStatusInfo().icon}</span>}
                    />
                  </Box>
                  {orchestratorStatus?.error && (
                    <Alert severity="error" sx={{ mb: 2 }}>Ошибка: {orchestratorStatus.error}</Alert>
                  )}
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>Управление обработкой:</Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    <Button variant="contained" startIcon={<RestartAltIcon />}
                      onClick={() => openConfirmDialog(handleRestartAll, 'Перезапустить всё', 
                        'Это действие сбросит все посты в статус "pending" и перезапустит AI обработку. Продолжить?')}
                      disabled={actionLoading} size="small">
                      Перезапустить всё
                    </Button>
                    <Button variant="outlined" startIcon={<RefreshIcon />}
                      onClick={loadAllData} disabled={loading} size="small">
                      Обновить данные
                    </Button>
                  </Stack>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* НОВАЯ СЕКЦИЯ: Управление фоновым процессом AI Orchestrator */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <ComputerIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Фоновый процесс AI Orchestrator
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>Статус фонового процесса:</Typography>
                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <Chip 
                      label={backgroundProcessStatus?.is_running ? 'Запущен' : 'Остановлен'}
                      color={backgroundProcessStatus?.is_running ? 'success' : 'default'}
                      icon={backgroundProcessStatus?.is_running ? <PlayArrowIcon /> : <PauseIcon />}
                    />
                    {backgroundProcessStatus?.process_id && (
                      <Chip 
                        label={`PID: ${backgroundProcessStatus.process_id}`}
                        size="small" 
                        variant="outlined"
                      />
                    )}
                  </Box>
                  
                  {/* Расширенная диагностика */}
                  {orchestratorStatus?.diagnostics && (
                    <Box mb={2}>
                      <Typography variant="caption" color="text.secondary" display="block">
                        Общее здоровье: {orchestratorStatus.diagnostics.overall_health}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" display="block">
                        Метод соединения: {orchestratorStatus.diagnostics.connection_method}
                      </Typography>
                      {orchestratorStatus.diagnostics.heartbeat_age_seconds && (
                        <Typography variant="caption" color="text.secondary" display="block">
                          Последний heartbeat: {orchestratorStatus.diagnostics.heartbeat_age_seconds}с назад
                        </Typography>
                      )}
                    </Box>
                  )}
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>Управление процессом:</Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    {!backgroundProcessStatus?.is_running ? (
                      <Button 
                        variant="contained" 
                        color="success"
                        startIcon={<PlayArrowIcon />}
                        onClick={startBackgroundProcess}
                        disabled={actionLoading}
                        size="small"
                      >
                        Запустить фоновый режим
                      </Button>
                    ) : (
                      <Button 
                        variant="contained" 
                        color="error"
                        startIcon={<PauseIcon />}
                        onClick={stopBackgroundProcess}
                        disabled={actionLoading}
                        size="small"
                      >
                        Остановить фоновый режим
                      </Button>
                    )}
                    
                    <Button 
                      variant="outlined"
                      startIcon={<RestartAltIcon />}
                      onClick={restartOrchestratorProcess}
                      disabled={actionLoading}
                      size="small"
                    >
                      Перезапустить
                    </Button>
                    
                    <Button 
                      variant="outlined"
                      startIcon={<ViewListIcon />}
                      onClick={() => setShowLogs(!showLogs)}
                      size="small"
                    >
                      {showLogs ? 'Скрыть логи' : 'Показать логи'}
                    </Button>
                  </Stack>
                </Grid>
              </Grid>
              
              {/* Логи AI Orchestrator */}
              <Collapse in={showLogs} timeout="auto" unmountOnExit>
                <Box mt={3}>
                  <Typography variant="subtitle2" gutterBottom>
                    <ViewListIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Логи AI Orchestrator (последние {orchestratorLogs.length})
                  </Typography>
                  
                  {orchestratorLogs.length > 0 ? (
                    <Paper variant="outlined" sx={{ maxHeight: 300, overflow: 'auto', p: 2 }}>
                      {orchestratorLogs.map((log, index) => (
                        <Box key={index} mb={1}>
                          <Typography 
                            variant="body2" 
                            component="div"
                            sx={{
                              fontFamily: 'monospace',
                              fontSize: '0.8rem',
                              color: log.level === 'ERROR' ? 'error.main' : 
                                     log.level === 'WARNING' ? 'warning.main' : 'text.primary'
                            }}
                          >
                            <Box component="span" sx={{ color: 'text.secondary' }}>
                              [{new Date(log.timestamp).toLocaleTimeString('ru-RU')}]
                            </Box>
                            {' '}
                            <Box component="span" sx={{ fontWeight: 'bold' }}>
                              {log.level}:
                            </Box>
                            {' '}
                            {log.message}
                          </Typography>
                        </Box>
                      ))}
                    </Paper>
                  ) : (
                    <Alert severity="info">
                      Нет доступных логов
                    </Alert>
                  )}
                </Box>
              </Collapse>
            </CardContent>
          </Card>

          {/* 🚀 МУЛЬТИТЕНАНТНАЯ Статистика AI сервисов */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <AnalyticsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Мультитенантная статистика AI сервисов
              </Typography>
              
              {/* Основная статистика */}
              <Grid container spacing={3} sx={{ mb: 3 }}>
                {[
                  { 
                    label: 'AI результатов', 
                    value: aiServicesStats?.ai_results_stats?.total_results || 0, 
                    color: 'primary' 
                  },
                  { 
                    label: 'В очереди', 
                    value: aiServicesStats?.posts_stats?.pending || 0, 
                    color: 'warning.main' 
                  },
                  { 
                    label: 'Обрабатывается', 
                    value: aiServicesStats?.posts_stats?.processing || 0, 
                    color: 'info.main',
                    tooltip: 'Промежуточные статусы: categorized + summarized'
                  },
                  { 
                    label: 'Завершено', 
                    value: aiServicesStats?.posts_stats?.completed || 0, 
                    color: 'success.main' 
                  }
                ].map((stat, index) => (
                  <Grid item xs={12} md={3} key={index}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color={stat.color}>{stat.value}</Typography>
                      <Typography variant="body2" color="text.secondary">{stat.label}</Typography>
                      {stat.tooltip && (
                        <Typography variant="caption" color="text.secondary" display="block">
                          {stat.tooltip}
                        </Typography>
                      )}
                    </Paper>
                  </Grid>
                ))}
              </Grid>

              {/* Детальная мультитенантная статистика */}
              {aiServicesStats?.multitenant_stats && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Детальная статистика по статусам:
                  </Typography>
                  <Grid container spacing={2}>
                    {Object.entries(aiServicesStats.multitenant_stats).map(([status, count]) => (
                      <Grid item xs={6} md={2} key={status}>
                        <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'grey.50' }}>
                          <Typography variant="h6" color={
                            status === 'completed' ? 'success.main' :
                            status === 'failed' ? 'error.main' :
                            status === 'categorized' ? 'info.main' :
                            status === 'summarized' ? 'primary.main' :
                            'warning.main'
                          }>
                            {count}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {status === 'pending' ? 'Ожидает' :
                             status === 'categorized' ? 'Категоризовано' :
                             status === 'summarized' ? 'Суммировано' :
                             status === 'completed' ? 'Завершено' :
                             status === 'failed' ? 'Ошибки' : status}
                          </Typography>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                  
                  <Box sx={{ mt: 2 }}>
                    <LinearProgress 
                      variant="determinate" 
                      value={aiServicesStats?.progress_percentage || 0}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                    <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 1 }}>
                      Прогресс: {Math.round(aiServicesStats?.progress_percentage || 0)}% 
                      ({aiServicesStats?.posts_stats?.completed || 0} из {aiServicesStats?.total_posts || 0} постов)
                    </Typography>
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Детальная статистика AI Orchestrator */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <ProcessingIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Детальная статистика AI Orchestrator
              </Typography>
              
              <Tabs 
                value={detailedTabValue} 
                onChange={(event, newValue) => setDetailedTabValue(newValue)}
                sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}
              >
                <Tab label="Статус системы" icon={<DashboardIcon />} />
                <Tab label="Активные задачи" icon={<ProcessingIcon />} />
                <Tab label="Последние операции" icon={<TimelineIcon />} />
                <Tab label="Статистика каналов" icon={<MemoryIcon />} />
              </Tabs>

              <TabPanel value={detailedTabValue} index={0}>
                {/* Статус системы */}
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Статус AI Orchestrator:
                    </Typography>
                    
                    <Box display="flex" flexDirection="column" gap={2}>
                      {/* Основной статус */}
                      <Box display="flex" alignItems="center" gap={1}>
                        <Chip 
                          label={getOrchestratorStatusInfo().text}
                          color={getOrchestratorStatusInfo().color}
                          icon={<span>{getOrchestratorStatusInfo().icon}</span>}
                          size="medium"
                        />
                        {orchestratorStatus?.orchestrator_active && (
                          <Typography variant="body2" color="success.main">
                            Активен
                          </Typography>
                        )}
                      </Box>
                      
                      {/* Детальная информация */}
                      {orchestratorStatus?.stats && (
                        <Box>
                          <Typography variant="body2" gutterBottom>
                            <strong>Внутренняя статистика:</strong>
                          </Typography>
                          <List dense>
                            <ListItem>
                              <Box display="flex" justifyContent="space-between" width="100%">
                                <Typography variant="body2">Размер очереди:</Typography>
                                <Typography variant="body2" fontWeight="bold">
                                  {orchestratorStatus.stats.queue_size || 0}
                                </Typography>
                              </Box>
                            </ListItem>
                            <ListItem>
                              <Box display="flex" justifyContent="space-between" width="100%">
                                <Typography variant="body2">Фоновый обработчик:</Typography>
                                <Chip 
                                  label={orchestratorStatus.stats.background_worker_running ? 'Запущен' : 'Остановлен'}
                                  color={orchestratorStatus.stats.background_worker_running ? 'success' : 'default'}
                                  size="small"
                                />
                              </Box>
                            </ListItem>
                            <ListItem>
                              <Box display="flex" justifyContent="space-between" width="100%">
                                <Typography variant="body2">Активная обработка:</Typography>
                                <Chip 
                                  label={orchestratorStatus.stats.processing_active ? 'Да' : 'Нет'}
                                  color={orchestratorStatus.stats.processing_active ? 'info' : 'default'}
                                  size="small"
                                />
                              </Box>
                            </ListItem>
                          </List>
                        </Box>
                      )}
                      
                      {/* Время последнего обновления */}
                      {orchestratorStatus?.last_update && (
                        <Typography variant="caption" color="text.secondary">
                          Последнее обновление: {new Date(orchestratorStatus.last_update).toLocaleString('ru-RU')}
                        </Typography>
                      )}
                      
                      {/* Время с последнего обновления */}
                      {orchestratorStatus?.time_since_update && (
                        <Typography variant="caption" color={orchestratorStatus.time_since_update > 120 ? 'error' : 'text.secondary'}>
                          {orchestratorStatus.time_since_update > 120 
                            ? `⚠️ Нет сигнала ${Math.round(orchestratorStatus.time_since_update / 60)} мин`
                            : `✅ Обновлено ${orchestratorStatus.time_since_update} сек назад`
                          }
                        </Typography>
                      )}
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Общая статистика обработки:
                    </Typography>
                    
                    {detailedAIStatus ? (
                      <Box>
                        <List dense>
                          <ListItem>
                            <Box display="flex" justifyContent="space-between" width="100%">
                              <Typography variant="body2">Всего постов:</Typography>
                              <Typography variant="body2" fontWeight="bold">
                                {detailedAIStatus.total_posts || 0}
                              </Typography>
                            </Box>
                          </ListItem>
                          <ListItem>
                            <Box display="flex" justifyContent="space-between" width="100%">
                              <Typography variant="body2">Обработано:</Typography>
                              <Typography variant="body2" fontWeight="bold" color="success.main">
                                {detailedAIStatus.posts_stats?.completed || 0}
                              </Typography>
                            </Box>
                          </ListItem>
                          <ListItem>
                            <Box display="flex" justifyContent="space-between" width="100%">
                              <Typography variant="body2">В очереди:</Typography>
                              <Typography variant="body2" fontWeight="bold" color="warning.main">
                                {detailedAIStatus.posts_stats?.pending || 0}
                              </Typography>
                            </Box>
                          </ListItem>
                          <ListItem>
                            <Box display="flex" justifyContent="space-between" width="100%">
                              <Typography variant="body2">Обрабатывается:</Typography>
                              <Typography variant="body2" fontWeight="bold" color="info.main">
                                {detailedAIStatus.posts_stats?.processing || 0}
                              </Typography>
                            </Box>
                          </ListItem>
                          {/* Новые мультитенантные статусы */}
                          {detailedAIStatus.multitenant_stats && (
                            <>
                              <ListItem>
                                <Box display="flex" justifyContent="space-between" width="100%">
                                  <Typography variant="body2">↳ Категоризовано:</Typography>
                                  <Typography variant="body2" fontWeight="bold" color="info.main">
                                    {detailedAIStatus.multitenant_stats.categorized || 0}
                                  </Typography>
                                </Box>
                              </ListItem>
                              <ListItem>
                                <Box display="flex" justifyContent="space-between" width="100%">
                                  <Typography variant="body2">↳ Суммировано:</Typography>
                                  <Typography variant="body2" fontWeight="bold" color="primary.main">
                                    {detailedAIStatus.multitenant_stats.summarized || 0}
                                  </Typography>
                                </Box>
                              </ListItem>
                            </>
                          )}
                          <ListItem>
                            <Box display="flex" justifyContent="space-between" width="100%">
                              <Typography variant="body2">Ошибки:</Typography>
                              <Typography variant="body2" fontWeight="bold" color="error.main">
                                {detailedAIStatus.posts_stats?.failed || 0}
                              </Typography>
                            </Box>
                          </ListItem>
                          <ListItem>
                            <Box display="flex" justifyContent="space-between" width="100%">
                              <Typography variant="body2">Прогресс:</Typography>
                              <Box display="flex" alignItems="center" gap={1}>
                                <LinearProgress 
                                  variant="determinate" 
                                  value={detailedAIStatus.progress_percentage || 0}
                                  sx={{ width: 80, height: 6 }}
                                />
                                <Typography variant="body2" fontWeight="bold">
                                  {Math.round(detailedAIStatus.progress_percentage || 0)}%
                                </Typography>
                              </Box>
                            </Box>
                          </ListItem>
                        </List>
                        
                        {detailedAIStatus.last_activity && (
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                            Последняя активность: {new Date(detailedAIStatus.last_activity).toLocaleString('ru-RU')}
                          </Typography>
                        )}
                      </Box>
                    ) : (
                      <Alert severity="info">
                        Загрузка детальной статистики...
                      </Alert>
                    )}
                  </Grid>
                </Grid>
              </TabPanel>

              <TabPanel value={detailedTabValue} index={1}>
                {/* Активные задачи */}
                {activeTasks.length > 0 ? (
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>ID задачи</TableCell>
                          <TableCell>Тип</TableCell>
                          <TableCell>Статус</TableCell>
                          <TableCell>Прогресс</TableCell>
                          <TableCell>Время выполнения</TableCell>
                          <TableCell>Бот ID</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {activeTasks.map((task, index) => (
                          <TableRow key={task.id || index}>
                            <TableCell>{task.id || `Task-${index}`}</TableCell>
                            <TableCell>
                              <Chip 
                                label={task.type || task.task_type || 'Unknown'} 
                                size="small"
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell>
                              <Chip 
                                label={task.status || 'pending'} 
                                color={task.status === 'completed' ? 'success' : 
                                       task.status === 'failed' ? 'error' : 
                                       task.status === 'processing' ? 'warning' : 'default'} 
                                size="small"
                              />
                            </TableCell>
                            <TableCell>
                              <Box display="flex" alignItems="center" gap={1}>
                                <LinearProgress 
                                  variant="determinate" 
                                  value={task.progress || 0} 
                                  sx={{ width: 60, height: 6 }}
                                />
                                <Typography variant="caption">
                                  {task.progress || 0}%
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell>{task.execution_time || task.processing_time || 'N/A'}</TableCell>
                            <TableCell>{task.bot_id || 'N/A'}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Alert severity="info">
                    Нет активных задач AI обработки
                  </Alert>
                )}
              </TabPanel>

              <TabPanel value={detailedTabValue} index={2}>
                {/* Последние операции */}
                {recentProcessedPosts.length > 0 ? (
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Время</TableCell>
                          <TableCell>Пост ID</TableCell>
                          <TableCell>Бот</TableCell>
                          <TableCell>Канал</TableCell>
                          <TableCell>Версия</TableCell>
                          <TableCell>Превью контента</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {recentProcessedPosts.slice(0, 10).map((post, index) => (
                          <TableRow key={post.post_id || index}>
                            <TableCell>
                              <Typography variant="caption">
                                {new Date(post.processed_at).toLocaleString('ru-RU')}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip label={post.post_id} size="small" variant="outlined" />
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {post.bot_name || `Bot ${post.bot_id}`}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {post.channel_name || `Channel ${post.channel_id}`}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip 
                                label={post.processing_version || 'v1.0'} 
                                size="small" 
                                color="primary"
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell>
                              <Typography variant="caption" sx={{ maxWidth: 200, display: 'block' }}>
                                {post.content_preview || 'Нет содержания'}
                              </Typography>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Alert severity="info">
                    Нет данных о последних операциях
                  </Alert>
                )}
              </TabPanel>

              <TabPanel value={detailedTabValue} index={3}>
                {/* Статистика каналов */}
                {channelsDetailedStats.length > 0 ? (
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Канал</TableCell>
                          <TableCell align="center">Всего постов</TableCell>
                          <TableCell align="center">Обработано</TableCell>
                          <TableCell align="center">В очереди</TableCell>
                          <TableCell align="center">Ошибки</TableCell>
                          <TableCell align="center">Прогресс</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {channelsDetailedStats.map((channel) => (
                          <TableRow key={channel.telegram_id}>
                            <TableCell>
                              <Box>
                                <Typography variant="body2" fontWeight="bold">
                                  {channel.name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {channel.username || channel.telegram_id}
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell align="center">
                              <Typography variant="body2" fontWeight="bold">
                                {channel.total_posts}
                              </Typography>
                            </TableCell>
                            <TableCell align="center">
                              <Chip 
                                label={channel.completed} 
                                color="success" 
                                size="small" 
                              />
                            </TableCell>
                            <TableCell align="center">
                              <Chip 
                                label={channel.pending} 
                                color={channel.pending > 0 ? "warning" : "default"} 
                                size="small" 
                              />
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
                                  {Math.round(channel.progress || 0)}%
                                </Typography>
                              </Box>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Alert severity="info">
                    Нет данных по каналам
                  </Alert>
                )}
              </TabPanel>
            </CardContent>
          </Card>
        </AccordionDetails>
      </Accordion>

      {/* РАЗДЕЛ 2: 🚀 МУЛЬТИТЕНАНТНАЯ СТАТИСТИКА ПО БОТАМ */}
      <Accordion defaultExpanded sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box display="flex" alignItems="center" gap={1}>
            <MonitorHeartIcon color="secondary" />
            <Typography variant="h6">Мультитенантная статистика по ботам</Typography>
            <Chip label={`${multitenantStats?.total_bots || 0} активных ботов`} color="secondary" size="small" />
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          {multitenantStats ? (
            <>
              {/* Общая статистика */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <DashboardIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Общая мультитенантная статистика
                  </Typography>
                  
                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    {Object.entries(multitenantStats.summary).map(([status, count]) => (
                      <Grid item xs={6} md={2} key={status}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h5" color={
                            status === 'completed' ? 'success.main' :
                            status === 'failed' ? 'error.main' :
                            status === 'categorized' ? 'info.main' :
                            status === 'summarized' ? 'primary.main' :
                            'warning.main'
                          }>
                            {count}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {status === 'pending' ? 'В очереди' :
                             status === 'categorized' ? 'Категоризовано' :
                             status === 'summarized' ? 'Суммировано' :
                             status === 'completed' ? 'Завершено' :
                             status === 'failed' ? 'Ошибки' : status}
                          </Typography>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                  
                  <Typography variant="body2" color="text.secondary" align="center">
                    Обрабатывается: {multitenantStats.ui_compatible_summary.processing} постов 
                    (категоризация + суммаризация)
                  </Typography>
                </CardContent>
              </Card>

              {/* Детальная статистика по ботам */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <SmartToyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Статистика по ботам ({multitenantStats.bots_stats.length})
                  </Typography>
                  
                  {multitenantStats.bots_stats.length > 0 ? (
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Бот</TableCell>
                            <TableCell align="center">Ожидает</TableCell>
                            <TableCell align="center">Категоризовано</TableCell>
                            <TableCell align="center">Суммировано</TableCell>
                            <TableCell align="center">Завершено</TableCell>
                            <TableCell align="center">Ошибки</TableCell>
                            <TableCell align="center">Прогресс</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {multitenantStats.bots_stats.map((bot) => (
                            <TableRow key={bot.bot_id}>
                              <TableCell>
                                <Box>
                                  <Typography variant="body2" fontWeight="bold">{bot.name}</Typography>
                                  <Chip label={bot.status} 
                                    color={bot.status === 'active' ? 'success' : 'info'} size="small" />
                                  <Typography variant="caption" color="text.secondary" display="block">
                                    {bot.channels_count} каналов
                                  </Typography>
                                </Box>
                              </TableCell>
                              <TableCell align="center">
                                <Chip label={bot.multitenant_stats.pending} 
                                  color="warning" size="small" />
                              </TableCell>
                              <TableCell align="center">
                                <Chip label={bot.multitenant_stats.categorized} 
                                  color="info" size="small" />
                              </TableCell>
                              <TableCell align="center">
                                <Chip label={bot.multitenant_stats.summarized} 
                                  color="primary" size="small" />
                              </TableCell>
                              <TableCell align="center">
                                <Chip label={bot.multitenant_stats.completed} 
                                  color="success" size="small" />
                              </TableCell>
                              <TableCell align="center">
                                <Chip label={bot.multitenant_stats.failed} 
                                  color={bot.multitenant_stats.failed > 0 ? "error" : "default"} size="small" />
                              </TableCell>
                              <TableCell align="center">
                                <Box display="flex" alignItems="center" gap={1}>
                                  <LinearProgress 
                                    variant="determinate" 
                                    value={bot.progress_percentage || 0}
                                    sx={{ width: 60, height: 6 }}
                                    color={bot.progress_percentage === 100 ? "success" : "primary"}
                                  />
                                  <Typography variant="caption">
                                    {Math.round(bot.progress_percentage || 0)}%
                                  </Typography>
                                </Box>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  ) : (
                    <Alert severity="info">
                      Нет активных ботов для отображения статистики
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </>
          ) : (
            <Alert severity="info">
              Загрузка мультитенантной статистики...
            </Alert>
          )}
        </AccordionDetails>
      </Accordion>

      {/* РАЗДЕЛ 3: МУЛЬТИТЕНАНТНЫЕ ДАННЫЕ */}
      <Accordion defaultExpanded sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box display="flex" alignItems="center" gap={1}>
            <SmartToyIcon color="primary" />
            <Typography variant="h6">Мультитенантные данные</Typography>
            <Chip label={`${botsWithStats.length} ботов`} color="primary" size="small" />
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          {/* Статистика по ботам */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  <SmartToyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Статистика по ботам ({botsWithStats.length})
                </Typography>
                <Button variant="outlined" startIcon={<RefreshIcon />}
                  onClick={loadAllData} disabled={loading} size="small">
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
                        <TableCell align="center">Прогресс</TableCell>
                        <TableCell align="center">Действия</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {botsWithStats.map((bot) => (
                        <React.Fragment key={bot.id}>
                          <TableRow>
                            <TableCell>
                              <Box>
                                <Typography variant="body2" fontWeight="bold">{bot.name}</Typography>
                                <Chip label={bot.status} 
                                  color={bot.status === 'active' ? 'success' : 'info'} size="small" />
                              </Box>
                            </TableCell>
                            <TableCell align="center">
                              <Typography variant="h6" color="primary">{bot.ai_results_count}</Typography>
                            </TableCell>
                            <TableCell align="center">
                              <Chip label={bot.channels_count} 
                                color={bot.channels_count > 0 ? "success" : "default"} size="small" />
                            </TableCell>
                            <TableCell align="center">
                              <Chip label={bot.categories_count} 
                                color={bot.categories_count > 0 ? "success" : "default"} size="small" />
                            </TableCell>
                            <TableCell align="center">
                              <Box display="flex" alignItems="center" gap={1}>
                                <LinearProgress variant="determinate" 
                                  value={bot.posts_stats.total > 0 ? 
                                    Math.round((bot.posts_stats.completed / bot.posts_stats.total) * 100) : 0} 
                                  sx={{ width: 60, height: 6 }}
                                  color={bot.posts_stats.completed === bot.posts_stats.total ? "success" : "primary"} />
                                <Typography variant="caption">
                                  {bot.posts_stats.total > 0 ? 
                                    Math.round((bot.posts_stats.completed / bot.posts_stats.total) * 100) : 0}%
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell align="center">
                              <IconButton size="small" onClick={() => handleBotExpand(bot.id)}
                                disabled={bot.channels_count === 0}>
                                {expandedBot === bot.id ? <ExpandLessIcon /> : <ExpandMoreIconTable />}
                              </IconButton>
                            </TableCell>
                          </TableRow>

                          {/* Развернутые детали бота */}
                          <TableRow>
                            <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
                              <Collapse in={expandedBot === bot.id} timeout="auto" unmountOnExit>
                                <Box sx={{ margin: 2 }}>
                                  <Typography variant="h6" gutterBottom>
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
                                              size="small" variant="outlined"
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
                                              size="small" color="primary" variant="outlined"
                                            />
                                          </Grid>
                                        ))}
                                      </Grid>
                                    </Box>
                                  )}

                                  {/* Кнопки управления ботом */}
                                  <Box display="flex" gap={1}>
                                    <Button size="small" variant="outlined" startIcon={<RestartAltIcon />}>
                                      Переобработать бота
                                    </Button>
                                    <Button size="small" variant="outlined" startIcon={<ViewIcon />}>
                                      Посмотреть результаты
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
          
          {/* Компонент мультитенантной очистки данных */}
          <DataCleanup />
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

export default AIResultsPage; 