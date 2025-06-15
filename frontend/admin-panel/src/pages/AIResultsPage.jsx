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
  Tune as TuneIcon
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
  const [channels, setChannels] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);
  const [actionLoading, setActionLoading] = useState(false);
  const [alert, setAlert] = useState({ show: false, type: 'info', message: '' });
  const [confirmDialog, setConfirmDialog] = useState({ open: false, action: null, title: '', message: '' });

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAIStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/status');
      const data = await response.json();
      setAiStatus(data);
    } catch (error) {
      console.error('Ошибка загрузки статуса AI:', error);
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

  const loadData = async () => {
    setLoading(true);
    await Promise.all([
      fetchAIStatus(),
      fetchActiveTasks(),
      fetchChannels()
    ]);
    setLoading(false);
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
      const response = await fetch('http://localhost:8000/api/ai/reprocess-channels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel_ids: selectedChannels })
      });
      const data = await response.json();
      
      if (data.success) {
        showAlert('success', `Перезапуск AI обработки инициирован для ${data.channels_processed} каналов. Сброшено ${data.total_posts_reset} постов, очищено ${data.total_ai_results_cleared} результатов.`);
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
                                  {channel.username ? `@${channel.username}` : `ID: ${channel.telegram_id}`}
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