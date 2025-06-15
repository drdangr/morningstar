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
  LinearProgress
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
  Pending as PendingIcon
} from '@mui/icons-material';
import apiService from '../services/api';

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
  const [aiStatus, setAiStatus] = useState(null);
  const [activeTasks, setActiveTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState({ open: false, action: null, title: '', message: '' });
  const [alert, setAlert] = useState({ show: false, type: 'info', message: '' });

  // Загрузка данных
  const fetchAIStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/status');
      const data = await response.json();
      setAiStatus(data);
    } catch (error) {
      console.error('Ошибка загрузки статуса AI:', error);
      showAlert('error', 'Ошибка загрузки статуса AI');
    }
  };

  const fetchActiveTasks = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/tasks');
      const data = await response.json();
      setActiveTasks(data.tasks || []);
    } catch (error) {
      console.error('Ошибка загрузки активных задач:', error);
      showAlert('error', 'Ошибка загрузки активных задач');
    }
  };

  const loadData = async () => {
    setLoading(true);
    await Promise.all([fetchAIStatus(), fetchActiveTasks()]);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
    // Автообновление каждые 30 секунд
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Утилиты
  const showAlert = (type, message) => {
    setAlert({ show: true, type, message });
    setTimeout(() => setAlert({ show: false, type: 'info', message: '' }), 5000);
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
                      value={aiStatus.posts_stats.completion_rate}
                      sx={{ mt: 1 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      Обработано: {aiStatus.posts_stats.completion_rate}%
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

      {/* Панель управления */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Панель управления AI
          </Typography>
          <Stack direction="row" spacing={2} flexWrap="wrap">
            <Button
              variant="contained"
              color="primary"
              startIcon={<PlayIcon />}
              onClick={() => openConfirmDialog(
                handleReprocessAll,
                'Перезапустить AI обработку',
                'Это действие сбросит статус всех постов на "ожидание" и очистит все AI результаты. Обработка начнется заново. Продолжить?'
              )}
              disabled={actionLoading}
            >
              Перезапустить всё
            </Button>
            
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => openConfirmDialog(
                handleClearResults,
                'Очистить AI результаты',
                'Это действие удалит все AI результаты, но не изменит статус постов. Продолжить?'
              )}
              disabled={actionLoading}
            >
              Очистить результаты
            </Button>
          </Stack>
        </CardContent>
      </Card>

      {/* Активные задачи */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <ScheduleIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Активные AI задачи ({activeTasks.length})
          </Typography>
          
          {activeTasks.length === 0 ? (
            <Alert severity="info">
              Нет активных AI задач
            </Alert>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>ID поста</TableCell>
                    <TableCell>Канал</TableCell>
                    <TableCell>Содержание</TableCell>
                    <TableCell>Дата поста</TableCell>
                    <TableCell>Просмотры</TableCell>
                    <TableCell>Собрано</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {activeTasks.map((task) => (
                    <TableRow key={task.post_id}>
                      <TableCell>
                        <Chip label={task.post_id} size="small" />
                      </TableCell>
                      <TableCell>
                        <Tooltip title={`Telegram ID: ${task.channel_telegram_id}`}>
                          <Typography variant="body2">
                            {task.channel_name}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 300 }}>
                          {task.content_preview || 'Нет содержания'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDate(task.post_date)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={task.views} size="small" color="primary" />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
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

      {/* Последняя активность */}
      {aiStatus?.recent_activity && aiStatus.recent_activity.length > 0 && (
        <Card sx={{ mt: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Последняя активность
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>ID поста</TableCell>
                    <TableCell>ID бота</TableCell>
                    <TableCell>Обработано</TableCell>
                    <TableCell>Версия</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {aiStatus.recent_activity.map((activity, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Chip label={activity.post_id} size="small" />
                      </TableCell>
                      <TableCell>
                        <Chip label={activity.bot_id} size="small" color="primary" />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDate(activity.processed_at)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={activity.version} size="small" variant="outlined" />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Диалог подтверждения */}
      <Dialog
        open={confirmDialog.open}
        onClose={() => setConfirmDialog({ open: false, action: null, title: '', message: '' })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>{confirmDialog.title}</DialogTitle>
        <DialogContent>
          <Typography>{confirmDialog.message}</Typography>
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
            color="primary"
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