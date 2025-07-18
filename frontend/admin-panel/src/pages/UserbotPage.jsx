import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  Alert,
  CircularProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Divider,
  IconButton,
  Collapse,
  LinearProgress
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Android as AndroidIcon,
  Radio as RadioIcon,
  Storage as StorageIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import apiService from '../services/api';

function UserbotPage() {
  const [userbotStatus, setUserbotStatus] = useState('unknown');
  const [channels, setChannels] = useState([]);
  const [recentPosts, setRecentPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(true);
  const [stats, setStats] = useState({
    totalChannels: 0,
    activeChannels: 0,
    totalPosts: 0,
    todayPosts: 0
  });
  const [showChannelDetails, setShowChannelDetails] = useState(false);
  const [lastCollection, setLastCollection] = useState(null);
  const [alert, setAlert] = useState({ show: false, message: '', severity: 'info' });

  useEffect(() => {
    loadUserbotData();
    // Автообновление каждые 30 секунд
    const interval = setInterval(loadUserbotData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadUserbotData = async () => {
    setStatsLoading(true);
    try {
      // Загружаем каналы
      const channelsResponse = await apiService.get('/channels');
      setChannels(channelsResponse);
      
      // Загружаем недавние посты  
      const postsResponse = await apiService.get('/posts/cache?limit=10&sort=created_at&order=desc');
      setRecentPosts(postsResponse.posts || []);
      
      // Вычисляем статистику
      const activeChannels = channelsResponse.filter(ch => ch.is_active);
      const today = new Date().toISOString().split('T')[0];
      const todayPosts = (postsResponse.posts || []).filter(post => 
        post.created_at && post.created_at.startsWith(today)
      );
      
      setStats({
        totalChannels: channelsResponse.length,
        activeChannels: activeChannels.length,
        totalPosts: postsResponse.total || 0,
        todayPosts: todayPosts.length
      });
      
      // Определяем статус userbot
      if (todayPosts.length > 0) {
        setUserbotStatus('active');
        setLastCollection(new Date(Math.max(...todayPosts.map(p => new Date(p.created_at)))));
      } else {
        setUserbotStatus('inactive');
      }
      
    } catch (error) {
      console.error('Ошибка загрузки данных userbot:', error);
      setUserbotStatus('error');
      showAlert('Ошибка загрузки данных userbot', 'error');
    } finally {
      setStatsLoading(false);
    }
  };

  const runUserbot = async () => {
    setLoading(true);
    try {
      // Отправляем запрос на запуск userbot
      const response = await apiService.post('/userbot/run');
      
      if (response.success) {
        showAlert(`Userbot запущен! Собрано постов: ${response.posts_collected}`, 'success');
        // Обновляем данные через 5 секунд
        setTimeout(loadUserbotData, 5000);
      } else {
        showAlert('Ошибка запуска userbot', 'error');
      }
    } catch (error) {
      console.error('Ошибка запуска userbot:', error);
      showAlert('Ошибка запуска userbot: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const showAlert = (message, severity) => {
    setAlert({ show: true, message, severity });
    setTimeout(() => setAlert({ show: false, message: '', severity: 'info' }), 5000);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <CheckCircleIcon color="success" />;
      case 'inactive': return <InfoIcon color="warning" />;
      case 'error': return <ErrorIcon color="error" />;
      default: return <AndroidIcon />;
    }
  };

  const formatTime = (date) => {
    if (!date) return 'Никогда';
    return new Date(date).toLocaleString('ru-RU');
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          <AndroidIcon sx={{ fontSize: 40, mr: 1, verticalAlign: 'middle' }} />
          Userbot Monitor
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Мониторинг и управление сбором постов из Telegram каналов
        </Typography>
      </Box>

      {/* Алерты */}
      {alert.show && (
        <Alert severity={alert.severity} sx={{ mb: 2 }} onClose={() => setAlert({ show: false, message: '', severity: 'info' })}>
          {alert.message}
        </Alert>
      )}

      {/* Основные статистики */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                {getStatusIcon(userbotStatus)}
                <Typography variant="h6" sx={{ ml: 1 }}>
                  Статус
                </Typography>
              </Box>
              <Chip 
                label={userbotStatus === 'active' ? 'Активен' : userbotStatus === 'inactive' ? 'Неактивен' : 'Ошибка'}
                color={getStatusColor(userbotStatus)}
                sx={{ mb: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                {lastCollection ? `Последний сбор: ${formatTime(lastCollection)}` : 'Данные не собирались'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <RadioIcon color="primary" />
                <Typography variant="h6" sx={{ ml: 1 }}>
                  Каналы
                </Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {statsLoading ? <CircularProgress size={24} /> : `${stats.activeChannels}/${stats.totalChannels}`}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Активных каналов
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <StorageIcon color="primary" />
                <Typography variant="h6" sx={{ ml: 1 }}>
                  Посты сегодня
                </Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {statsLoading ? <CircularProgress size={24} /> : stats.todayPosts}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Собрано за сегодня
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <StorageIcon color="primary" />
                <Typography variant="h6" sx={{ ml: 1 }}>
                  Всего постов
                </Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {statsLoading ? <CircularProgress size={24} /> : stats.totalPosts}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                В базе данных
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Управление */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Управление
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <Button
              variant="contained"
              startIcon={loading ? <CircularProgress size={20} /> : <PlayIcon />}
              onClick={runUserbot}
              disabled={loading}
              color="primary"
            >
              {loading ? 'Запускаю...' : 'Запустить сбор'}
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={loadUserbotData}
              disabled={statsLoading}
            >
              Обновить данные
            </Button>
          </Box>
          <Typography variant="body2" color="text.secondary">
            Запуск userbot для однократного сбора постов из всех активных каналов
          </Typography>
        </CardContent>
      </Card>

      {/* Активные каналы */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">
              Активные каналы ({stats.activeChannels})
            </Typography>
            <IconButton onClick={() => setShowChannelDetails(!showChannelDetails)}>
              {showChannelDetails ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>
          
          <Collapse in={showChannelDetails}>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Канал</TableCell>
                    <TableCell>Username</TableCell>
                    <TableCell>Описание</TableCell>
                    <TableCell>Статус</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {channels.filter(ch => ch.is_active).map((channel) => (
                    <TableRow key={channel.id}>
                      <TableCell>{channel.channel_name}</TableCell>
                      <TableCell>{channel.username}</TableCell>
                      <TableCell>{channel.description || 'Нет описания'}</TableCell>
                      <TableCell>
                        <Chip 
                          label="Активен" 
                          size="small" 
                          color="success"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Collapse>
        </CardContent>
      </Card>

      {/* Последние посты */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Последние собранные посты
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Канал</TableCell>
                  <TableCell>Содержимое</TableCell>
                  <TableCell>Дата поста</TableCell>
                  <TableCell>Собрано</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recentPosts.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      <Typography color="text.secondary">
                        Нет данных для отображения
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  recentPosts.map((post) => (
                    <TableRow key={post.id}>
                      <TableCell>{post.id}</TableCell>
                      <TableCell>{post.channel_title || 'N/A'}</TableCell>
                      <TableCell>{post.content ? post.content.substring(0, 100) + '...' : 'Нет содержимого'}</TableCell>
                      <TableCell>{formatTime(post.post_date)}</TableCell>
                      <TableCell>{formatTime(post.created_at)}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}

export default UserbotPage; 