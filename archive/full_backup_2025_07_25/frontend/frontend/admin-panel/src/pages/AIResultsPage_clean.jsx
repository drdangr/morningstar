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
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Rating,
  List,
  ListItem,
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
  Stack,
  LinearProgress,
  Checkbox,
  FormControlLabel,
  FormGroup,
  Snackbar,
  Collapse
} from '@mui/material';

import {
  SmartToy as SmartToyIcon,
  Analytics as AnalyticsIcon,
  Speed as ProcessingIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as ViewIcon,
  Refresh as RefreshIcon,
  Stop as StopIcon,
  Delete as DeleteIcon,
  Assessment as AssessmentIcon,
  Psychology as PsychologyIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Pending as PendingIcon,
  RestartAlt as RestartAltIcon,
  ExpandLess as ExpandLessIcon,
  ExpandMore as ExpandMoreIconTable,
  Settings as SettingsIcon,
  Build as BuildIcon,
  Memory as MemoryIcon,
  Timeline as TimelineIcon,
  Dashboard as DashboardIcon
} from '@mui/icons-material';

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
  // Состояния для UI
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [alert, setAlert] = useState({ show: false, type: 'info', message: '' });
  const [confirmDialog, setConfirmDialog] = useState({ open: false, action: null, title: '', message: '' });
  
  // Состояния для AI Orchestrator и сервисов
  const [orchestratorStatus, setOrchestratorStatus] = useState(null);
  const [aiServicesStats, setAiServicesStats] = useState(null);
  const [activeTasks, setActiveTasks] = useState([]);
  const [performanceMetrics, setPerformanceMetrics] = useState(null);
  const [detailedTabValue, setDetailedTabValue] = useState(0);
  
  // Состояния для мультитенантных данных
  const [botsWithStats, setBotsWithStats] = useState([]);
  const [channels, setChannels] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);
  const [selectedBots, setSelectedBots] = useState([]);
  const [expandedBot, setExpandedBot] = useState(null);

  // Загрузка данных при монтировании
  useEffect(() => {
    loadAllData();
    
    // Автообновление каждые 10 секунд
    const interval = setInterval(loadAllData, 10000);
    return () => clearInterval(interval);
  }, []);

  // Функции загрузки данных
  const loadAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchOrchestratorStatus(),
        fetchAIServicesStats(),
        fetchActiveTasks(),
        fetchPerformanceMetrics(),
        fetchBotsWithStats(),
        fetchChannels()
      ]);
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
      showAlert('error', 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const fetchOrchestratorStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/orchestrator-live-status');
      if (response.ok) {
        const data = await response.json();
        setOrchestratorStatus(data);
      } else {
        setOrchestratorStatus({ 
          orchestrator_active: false,
          status: 'UNAVAILABLE',
          error: `HTTP ${response.status}`
        });
      }
    } catch (error) {
      setOrchestratorStatus({
        orchestrator_active: false,
        status: 'ERROR',
        error: error.message
      });
    }
  };

  const fetchAIServicesStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/status');
      if (response.ok) {
        const data = await response.json();
        setAiServicesStats(data);
      }
    } catch (error) {
      console.error('Ошибка загрузки статистики AI сервисов:', error);
    }
  };

  const fetchActiveTasks = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/tasks');
      if (response.ok) {
        const data = await response.json();
        setActiveTasks(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      setActiveTasks([]);
    }
  };

  const fetchPerformanceMetrics = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/performance-metrics');
      if (response.ok) {
        const data = await response.json();
        setPerformanceMetrics(data);
      }
    } catch (error) {
      console.error('Ошибка загрузки метрик производительности:', error);
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
            posts_stats: {
              total: results.length,
              pending: 0,
              processing: 0,
              completed: results.length,
              failed: 0
            }
          };
        } catch (error) {
          return {
            ...bot,
            ai_results_count: 0,
            channels_count: 0,
            categories_count: 0,
            channels: [],
            categories: [],
            posts_stats: { total: 0, pending: 0, processing: 0, completed: 0, failed: 0 }
          };
        }
      });
      
      const botsWithStats = await Promise.all(botsWithStatsPromises);
      setBotsWithStats(botsWithStats);
      
    } catch (error) {
      console.error('Ошибка получения статистики ботов:', error);
      setBotsWithStats([]);
    }
  };

  const fetchChannels = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/channels');
      if (response.ok) {
        const data = await response.json();
        setChannels(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      setChannels([]);
    }
  };

  // Функции-обработчики для AI Orchestrator
  const showAlert = (type, message) => {
    setAlert({ show: true, type, message });
  };

  const openConfirmDialog = (action, title, message) => {
    setConfirmDialog({ open: true, action, title, message });
  };

  const handleRestartAll = async () => {
    setActionLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/ai/reprocess-all', { method: 'POST' });
      const data = await response.json();
      
      if (data.success) {
        showAlert('success', `Перезапуск AI обработки инициирован. Сброшено ${data.posts_reset} постов.`);
        await loadAllData();
      } else {
        showAlert('error', data.message || 'Ошибка перезапуска AI обработки');
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
        await loadAllData();
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
        await loadAllData();
      } else {
        showAlert('error', data.message || 'Ошибка очистки результатов');
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
      const response = await fetch('http://localhost:8000/api/ai/reprocess-channels-auto', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel_ids: selectedChannels })
      });
      const data = await response.json();
      
      if (data.success) {
        showAlert('success', `Перезапуск AI обработки инициирован для ${data.channels_processed} каналов.`);
        setSelectedChannels([]);
        await loadAllData();
      } else {
        showAlert('error', data.message || 'Ошибка перезапуска AI обработки для каналов');
      }
    } catch (error) {
      showAlert('error', 'Ошибка выполнения операции');
    }
    setActionLoading(false);
    setConfirmDialog({ open: false, action: null, title: '', message: '' });
  };

  // Функции-обработчики для мультитенантных данных
  const handleBotExpand = (botId) => {
    setExpandedBot(expandedBot === botId ? null : botId);
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

  const handleBotSelect = (botId) => {
    setSelectedBots(prev => 
      prev.includes(botId) 
        ? prev.filter(id => id !== botId)
        : [...prev, botId]
    );
  };

  const handleSelectAllBots = () => {
    setSelectedBots(
      selectedBots.length === botsWithStats.length ? [] : botsWithStats.map(b => b.id)
    );
  };

  const handleClearChannelData = async () => {
    if (selectedChannels.length === 0) {
      showAlert('warning', 'Выберите каналы для очистки данных');
      return;
    }

    setActionLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/channels/clear-data', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel_ids: selectedChannels })
      });
      const data = await response.json();
      
      if (data.success) {
        showAlert('success', `Очищены данные для ${data.channels_cleared} каналов.`);
        setSelectedChannels([]);
        await loadAllData();
      } else {
        showAlert('error', data.message || 'Ошибка очистки данных каналов');
      }
    } catch (error) {
      showAlert('error', 'Ошибка выполнения операции');
    }
    setActionLoading(false);
    setConfirmDialog({ open: false, action: null, title: '', message: '' });
  };

  const handleClearBotData = async () => {
    if (selectedBots.length === 0) {
      showAlert('warning', 'Выберите ботов для очистки данных');
      return;
    }

    setActionLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/bots/clear-ai-results', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bot_ids: selectedBots })
      });
      const data = await response.json();
      
      if (data.success) {
        showAlert('success', `Очищены AI результаты для ${data.bots_cleared} ботов.`);
        setSelectedBots([]);
        await loadAllData();
      } else {
        showAlert('error', data.message || 'Ошибка очистки данных ботов');
      }
    } catch (error) {
      showAlert('error', 'Ошибка выполнения операции');
    }
    setActionLoading(false);
    setConfirmDialog({ open: false, action: null, title: '', message: '' });
  };

  // Вспомогательные функции
  const getOrchestratorStatusInfo = () => {
    if (!orchestratorStatus) {
      return { text: 'НЕИЗВЕСТНО', color: 'default', icon: '❓' };
    }

    if (orchestratorStatus.orchestrator_active) {
      const status = orchestratorStatus.status;
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

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU');
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
      <Snackbar 
        open={alert.show} 
        autoHideDuration={6000} 
        onClose={() => setAlert({ show: false, type: 'info', message: '' })}
      >
        <Alert severity={alert.type} onClose={() => setAlert({ show: false, type: 'info', message: '' })}>
          {alert.message}
        </Alert>
      </Snackbar>

      {loading && (
        <Box display="flex" justifyContent="center" my={2}>
          <CircularProgress />
        </Box>
      )}

      {/* РАЗДЕЛ 1: AI ORCHESTRATOR И СЕРВИСЫ */}
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
          {/* Содержимое раздела AI сервисов будет добавлено в следующих частях */}
          <Typography>AI Orchestrator - содержимое будет добавлено</Typography>
        </AccordionDetails>
      </Accordion>

      {/* РАЗДЕЛ 2: МУЛЬТИТЕНАНТНЫЕ ДАННЫЕ */}
      <Accordion defaultExpanded sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box display="flex" alignItems="center" gap={1}>
            <SmartToyIcon color="primary" />
            <Typography variant="h6">Мультитенантные данные</Typography>
            <Chip 
              label={`${botsWithStats.length} ботов`}
              color="primary"
              size="small"
            />
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          {/* Содержимое раздела мультитенантных данных будет добавлено в следующих частях */}
          <Typography>Мультитенантные данные - содержимое будет добавлено</Typography>
        </AccordionDetails>
      </Accordion>

    </Box>
  );
};

export default AIResultsPage; 