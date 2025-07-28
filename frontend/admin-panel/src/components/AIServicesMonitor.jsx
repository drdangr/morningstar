import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  IconButton,
  Divider,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  SmartToy as AIIcon,
  Psychology as CategoryIcon,
  Summarize as SummaryIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Queue as QueueIcon,
  TrendingUp as StatsIcon,
  Speed as PerformanceIcon,
  Visibility as ViewIcon,
  PlayArrow as StartIcon,
  Pause as PauseIcon,
  FlowerIcon,
  Memory as MemoryIcon
} from '@mui/icons-material';

// Импорт API конфигурации
import { API_BASE_URL } from '../config/api';

// Компонент карточки сервиса
function ServiceCard({ service, onRefresh, onViewTasks }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'success';
      case 'paused': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'running': return 'Работает';
      case 'paused': return 'Приостановлен';
      case 'error': return 'Ошибка';
      default: return 'Неизвестно';
    }
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            {service.type === 'categorization' ? <CategoryIcon color="primary" /> : <SummaryIcon color="secondary" />}
            <Typography variant="h6">
              {service.name}
            </Typography>
          </Box>
          <Chip 
            label={getStatusText(service.status)} 
            color={getStatusColor(service.status)} 
            size="small"
          />
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {service.description}
        </Typography>

                 {/* Настройки сервиса */}
         <Box sx={{ mb: 2 }}>
           <Typography variant="subtitle2" gutterBottom>⚙️ Настройки:</Typography>
           <Typography variant="body2">• Модель: {service.settings.model}</Typography>
           <Typography variant="body2">• Max токенов: {service.settings.max_tokens}</Typography>
           <Typography variant="body2">• Температура: {service.settings.temperature}</Typography>
           <Typography variant="body2">• Top-p: {service.settings.top_p}</Typography>
           <Typography variant="body2">• Задержка: {service.settings.delay}с</Typography>
         </Box>

        {/* Статистика */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>📊 Статистика:</Typography>
          <Box display="flex" justifyContent="space-between" mb={1}>
            <Typography variant="body2">Всего:</Typography>
            <Typography variant="body2" fontWeight="bold">{service.stats.total}</Typography>
          </Box>
          <Box display="flex" justifyContent="space-between" mb={1}>
            <Typography variant="body2">Обработано:</Typography>
            <Typography variant="body2" fontWeight="bold" color="success.main">
              {service.stats.processed}
            </Typography>
          </Box>
          <Box display="flex" justifyContent="space-between" mb={1}>
            <Typography variant="body2">В работе:</Typography>
            <Typography variant="body2" fontWeight="bold" color="warning.main">
              {service.stats.processing}
            </Typography>
          </Box>
          <Box display="flex" justifyContent="space-between" mb={1}>
            <Typography variant="body2">В очереди:</Typography>
            <Typography variant="body2" fontWeight="bold" color="info.main">
              {service.stats.pending}
            </Typography>
          </Box>

          {/* Прогресс бар */}
          <Box sx={{ mt: 1 }}>
            <LinearProgress 
              variant="determinate" 
              value={service.stats.total > 0 ? (service.stats.processed / service.stats.total) * 100 : 0}
              sx={{ height: 8, borderRadius: 4 }}
            />
            <Typography variant="caption" color="text.secondary">
              {service.stats.total > 0 ? 
                `${Math.round((service.stats.processed / service.stats.total) * 100)}% завершено` : 
                'Нет данных'
              }
            </Typography>
          </Box>
        </Box>

        {/* Кнопки управления */}
        <Box display="flex" gap={1} flexWrap="wrap">
          <Button 
            size="small" 
            variant="outlined" 
            startIcon={<RefreshIcon />}
            onClick={() => onRefresh(service.type)}
          >
            Обновить
          </Button>
          <Button 
            size="small" 
            variant="outlined" 
            startIcon={<ViewIcon />}
            onClick={() => onViewTasks(service.type)}
          >
            Задачи
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
}

// Главный компонент AI Services Monitor
function AIServicesMonitor() {
  const [services, setServices] = useState([]);
  const [systemStats, setSystemStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30); // секунды
  const [currentTasks, setCurrentTasks] = useState([]);
  const [showTasks, setShowTasks] = useState(false);
  const [selectedService, setSelectedService] = useState('');

  // Загрузка данных AI сервисов
  const loadAIServices = async () => {
    setLoading(true);
    setError('');

    try {
      // Получаем статистику AI сервисов
      const statsResponse = await fetch(`${API_BASE_URL}/api/ai/status`);
      if (!statsResponse.ok) {
        throw new Error(`Ошибка загрузки статистики: ${statsResponse.status}`);
      }
      const statsData = await statsResponse.json();

      // Получаем настройки AI сервисов
      const settingsResponse = await fetch(`${API_BASE_URL}/api/settings`);
      const settingsData = settingsResponse.ok ? await settingsResponse.json() : [];

      // Формируем данные сервисов
      const servicesData = [
        {
          type: 'categorization',
          name: 'Категоризация постов',
          description: 'Псевдообработка категоризации с определением тем и метрик',
          status: 'running', // В реальности нужно получить из Celery
                     settings: {
             model: getSettingValue(settingsData, 'ai_categorization_model', 'gpt-4o-mini'),
             max_tokens: getSettingValue(settingsData, 'ai_categorization_max_tokens', '1000'),
             temperature: getSettingValue(settingsData, 'ai_categorization_temperature', '0.3'),
             top_p: getSettingValue(settingsData, 'ai_categorization_top_p', '1.0'),
             delay: '5' // Задержка псевдообработки
           },
          stats: {
            total: statsData.total_posts || 0,
            processed: statsData.categorized_posts || 0,
            processing: statsData.processing_posts || 0,
            pending: (statsData.total_posts || 0) - (statsData.categorized_posts || 0) - (statsData.processing_posts || 0)
          }
        },
        {
          type: 'summarization',
          name: 'Саммаризация постов',
          description: 'Псевдообработка создания резюме постов с подсчетом токенов',
          status: 'running',
                     settings: {
             model: getSettingValue(settingsData, 'ai_summarization_model', 'gpt-4o'),
             max_tokens: getSettingValue(settingsData, 'ai_summarization_max_tokens', '2000'),
             temperature: getSettingValue(settingsData, 'ai_summarization_temperature', '0.7'),
             top_p: getSettingValue(settingsData, 'ai_summarization_top_p', '1.0'),
             delay: '2' // Задержка псевдообработки
           },
          stats: {
            total: statsData.total_posts || 0,
            processed: statsData.summarized_posts || 0,
            processing: statsData.processing_posts || 0,
            pending: (statsData.total_posts || 0) - (statsData.summarized_posts || 0) - (statsData.processing_posts || 0)
          }
        }
      ];

      setServices(servicesData);
      setSystemStats(statsData);

    } catch (err) {
      console.error('❌ Ошибка загрузки AI сервисов:', err);
      setError('Ошибка загрузки данных AI сервисов: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Вспомогательная функция для получения значения настройки
  const getSettingValue = (settings, key, defaultValue) => {
    const setting = settings.find(s => s.key === key);
    return setting ? setting.value : defaultValue;
  };

  // Обновление конкретного сервиса
  const handleRefreshService = async (serviceType) => {
    console.log(`🔄 Обновляем сервис: ${serviceType}`);
    await loadAIServices();
  };

  // Просмотр задач сервиса
  const handleViewTasks = (serviceType) => {
    setSelectedService(serviceType);
    setShowTasks(true);
    console.log(`👁️ Просмотр задач сервиса: ${serviceType}`);
    // Здесь можно загрузить данные о текущих задачах из Flower API
  };

  // Автообновление
  useEffect(() => {
    loadAIServices();

    if (autoRefresh) {
      const interval = setInterval(loadAIServices, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  return (
    <Box>
      {/* Заголовок */}
      <Box display="flex" alignItems="center" gap={2} sx={{ mb: 3 }}>
        <AIIcon color="primary" sx={{ fontSize: 32 }} />
        <Typography variant="h4">
          AI Services Monitor
        </Typography>
        <Chip 
          label="Псевдообработка" 
          color="info" 
          variant="outlined"
        />
      </Box>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Мониторинг AI сервисов для категоризации и саммаризации постов. 
        Псевдообработка с задержками для безопасного тестирования без затрат на токены.
      </Typography>

      {/* Панель управления */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box display="flex" alignItems="center" justify="space-between" flexWrap="wrap" gap={2}>
          <Box display="flex" alignItems="center" gap={2}>
            <FormControlLabel
              control={
                <Switch
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                />
              }
              label="Автообновление"
            />
            
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Интервал</InputLabel>
              <Select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(e.target.value)}
                label="Интервал"
                disabled={!autoRefresh}
              >
                <MenuItem value={10}>10 сек</MenuItem>
                <MenuItem value={30}>30 сек</MenuItem>
                <MenuItem value={60}>1 мин</MenuItem>
                <MenuItem value={300}>5 мин</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <Box display="flex" gap={1}>
            <Button
              variant="contained"
              startIcon={<RefreshIcon />}
              onClick={loadAIServices}
              disabled={loading}
            >
              Обновить все
            </Button>
            <Button
              variant="outlined"
              startIcon={<QueueIcon />}
              href="http://localhost:5555" // Flower URL
              target="_blank"
            >
              Flower Monitor
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Ошибки */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Системная статистика */}
      {systemStats && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            📊 Общая статистика системы
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h4" color="primary">
                  {systemStats.total_posts || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Всего постов
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h4" color="success.main">
                  {systemStats.processed_posts || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Обработано
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h4" color="warning.main">
                  {systemStats.processing_posts || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  В обработке
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h4" color="info.main">
                  {systemStats.active_bots || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Активных ботов
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Карточки сервисов */}
      <Grid container spacing={3}>
        {loading ? (
          <Grid item xs={12}>
            <Box display="flex" justifyContent="center" alignItems="center" py={4}>
              <CircularProgress />
              <Typography variant="body1" sx={{ ml: 2 }}>
                Загрузка данных AI сервисов...
              </Typography>
            </Box>
          </Grid>
        ) : (
          services.map((service) => (
            <Grid item xs={12} md={6} key={service.type}>
              <ServiceCard
                service={service}
                onRefresh={handleRefreshService}
                onViewTasks={handleViewTasks}
              />
            </Grid>
          ))
        )}
      </Grid>

      {/* Информационное сообщение */}
      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="body2">
          💡 <strong>Псевдообработка активна:</strong> AI сервисы работают в режиме имитации для безопасного тестирования. 
          Реальные вызовы OpenAI API отключены. Используются фиксированные задержки: категоризация 5с, саммаризация 2с.
        </Typography>
      </Alert>
    </Box>
  );
}

export default AIServicesMonitor; 