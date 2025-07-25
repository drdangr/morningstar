import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  Chip,
  Divider,
} from '@mui/material';
import {
  Topic as TopicIcon,
  Tv as ChannelsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import apiService from '../services/api';

const StatCard = ({ title, value, icon, color }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography color="textSecondary" gutterBottom variant="h6">
            {title}
          </Typography>
          <Typography variant="h4" component="h2">
            {value}
          </Typography>
        </Box>
        <Box sx={{ color: color, opacity: 0.7 }}>
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [recentDigests, setRecentDigests] = useState([]);
  const [systemHealth, setSystemHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
    // Обновляем данные каждые 30 секунд
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Загружаем все данные параллельно
      const [statsData, digestsData, healthData] = await Promise.all([
        apiService.getStats(),
        apiService.get('/digests?limit=5'),
        apiService.healthCheck().catch(() => ({ status: 'error' }))
      ]);
      
      setStats(statsData);
      setRecentDigests(digestsData || []);
      setSystemHealth(healthData);
      setError(null);
    } catch (err) {
      setError('Не удалось загрузить данные дашборда: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'Неизвестно';
    try {
      const date = new Date(dateString);
      return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Неизвестно';
    }
  };

  const getTimeAgo = (dateString) => {
    if (!dateString) return 'Неизвестно';
    try {
      const now = new Date();
      // Добавляем 'Z' если нет временной зоны, чтобы парсить как UTC
      const utcDateString = dateString.includes('Z') || dateString.includes('+') ? dateString : dateString + 'Z';
      const date = new Date(utcDateString);
      const diffMs = now - date;
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      const diffHours = Math.floor(diffMinutes / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffMinutes < 1) return 'только что';
      if (diffMinutes < 60) return `${diffMinutes} мин назад`;
      if (diffHours < 24) return `${diffHours} ч назад`;
      return `${diffDays} дн назад`;
    } catch {
      return 'Неизвестно';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Добро пожаловать в админ-панель MorningStar Bot
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Topics"
            value={stats?.active_categories || 0}
            icon={<TopicIcon sx={{ fontSize: 40 }} />}
            color="primary.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Channels"
            value={stats?.active_channels || 0}
            icon={<ChannelsIcon sx={{ fontSize: 40 }} />}
            color="secondary.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Posts"
            value={stats?.total_posts || 0}
            icon={<TrendingUpIcon sx={{ fontSize: 40 }} />}
            color="success.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Database Size"
            value={`${stats?.database_size_mb || 0} MB`}
            icon={<TrendingUpIcon sx={{ fontSize: 40 }} />}
            color="warning.main"
          />
        </Grid>
      </Grid>

      {/* Дополнительная статистика по постам */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={4} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    Pending Posts
                  </Typography>
                  <Typography variant="h4" component="h2">
                    {stats?.posts_pending || 0}
                  </Typography>
                </Box>
                <Box sx={{ color: 'warning.main', opacity: 0.7 }}>
                  <ScheduleIcon sx={{ fontSize: 40 }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    Processed Posts
                  </Typography>
                  <Typography variant="h4" component="h2">
                    {stats?.posts_processed || 0}
                  </Typography>
                </Box>
                <Box sx={{ color: 'success.main', opacity: 0.7 }}>
                  <CheckCircleIcon sx={{ fontSize: 40 }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    Total Digests
                  </Typography>
                  <Typography variant="h4" component="h2">
                    {stats?.total_digests || 0}
                  </Typography>
                </Box>
                <Box sx={{ color: 'primary.main', opacity: 0.7 }}>
                  <TrendingUpIcon sx={{ fontSize: 40 }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    Channel Links
                  </Typography>
                  <Typography variant="h4" component="h2">
                    {stats?.channel_category_links || 0}
                  </Typography>
                </Box>
                <Box sx={{ color: 'info.main', opacity: 0.7 }}>
                  <TopicIcon sx={{ fontSize: 40 }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Box display="flex" alignItems="center" mb={2}>
              <ScheduleIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6">
                Recent Activity
              </Typography>
            </Box>
            {recentDigests.length > 0 ? (
              <List dense>
                {recentDigests.map((digest, index) => (
                  <React.Fragment key={digest.id}>
                    <ListItem>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" justifyContent="space-between">
                            <Typography variant="body1">
                              Дайджест #{digest.id}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              {getTimeAgo(digest.created_at)}
                            </Typography>
                          </Box>
                        }
                        secondary={
                          <Box mt={1}>
                            <Box display="flex" gap={1} flexWrap="wrap">
                              <Chip
                                size="small"
                                label={`${digest.total_posts} постов`}
                                color="primary"
                                variant="outlined"
                              />
                              <Chip
                                size="small"
                                label={`${digest.relevant_posts} релевантных`}
                                color="success"
                                variant="outlined"
                              />
                              <Chip
                                size="small"
                                label={`${digest.channels_processed} каналов`}
                                color="info"
                                variant="outlined"
                              />
                              <Chip
                                size="small"
                                label={`важность: ${digest.avg_importance.toFixed(1)}`}
                                color="warning"
                                variant="outlined"
                              />
                            </Box>
                            <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5, display: 'block' }}>
                              {formatDateTime(digest.created_at)}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < recentDigests.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            ) : (
              <Box textAlign="center" py={3}>
                <Typography variant="body2" color="textSecondary">
                  Дайджесты пока не создавались
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Box display="flex" alignItems="center" mb={2}>
              <TrendingUpIcon sx={{ mr: 1, color: 'success.main' }} />
              <Typography variant="h6">
                System Status
              </Typography>
            </Box>
            <List dense>
              <ListItem>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Typography variant="body2">Backend API</Typography>
                      {systemHealth?.status === 'ok' ? (
                        <Chip
                          size="small"
                          icon={<CheckCircleIcon />}
                          label="Работает"
                          color="success"
                          variant="outlined"
                        />
                      ) : (
                        <Chip
                          size="small"
                          icon={<ErrorIcon />}
                          label="Ошибка"
                          color="error"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  }
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Typography variant="body2">Дайджестов создано</Typography>
                      <Typography variant="body1" fontWeight="bold">
                        {stats?.total_digests || 0}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Typography variant="body2">Связей канал-категория</Typography>
                      <Typography variant="body1" fontWeight="bold">
                        {stats?.channel_category_links || 0}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
              {recentDigests.length > 0 && (
                <>
                  <Divider />
                  <ListItem>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" justifyContent="space-between">
                          <Typography variant="body2">Последний сбор</Typography>
                          <Typography variant="body2" color="textSecondary">
                            {getTimeAgo(recentDigests[0]?.created_at)}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                </>
              )}
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
} 