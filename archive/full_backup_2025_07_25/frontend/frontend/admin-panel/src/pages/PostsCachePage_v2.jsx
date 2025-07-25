import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  Chip
} from '@mui/material';
import {
  Storage as StorageIcon,
  Psychology as PsychologyIcon
} from '@mui/icons-material';

// Импорт компонентов табов
import { RawPostsTab, AIResultsTab } from '../components/Posts';

// Определяем API URL динамически
const API_BASE_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000' 
  : 'http://localhost:8000';

function PostsCachePage() {
  // Состояние для управления табами
  const [currentTab, setCurrentTab] = useState(0);
  
  // Общее состояние
  const [stats, setStats] = useState(null);
  const [aiStats, setAiStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Загрузка общей статистики
  const loadStats = async () => {
    setLoading(true);
    try {
      console.log('🔄 Загружаем общую статистику...');
      const response = await fetch(`${API_BASE_URL}/api/posts/stats`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ Общая статистика получена:', data);
      setStats(data);
    } catch (err) {
      console.error('❌ Ошибка загрузки статистики:', err);
      setError('Ошибка загрузки статистики: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Загрузка AI статистики для подсчета используемых каналов
  const loadAIStats = async () => {
    try {
      console.log('🔄 Загружаем AI статистику...');
      const response = await fetch(`${API_BASE_URL}/api/ai/multitenant-status`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ AI статистика получена:', data);
      setAiStats(data);
    } catch (err) {
      console.error('❌ Ошибка загрузки AI статистики:', err);
    }
  };

  // Подсчет уникальных каналов, используемых активными ботами
  const getUsedChannelsCount = () => {
    if (!aiStats?.bots_stats) return 0;
    
    // Подсчитываем общее количество каналов в активных ботах
    let totalChannelsInActiveBots = 0;
    
    for (const bot of aiStats.bots_stats) {
      if (bot.status === 'active') {
        totalChannelsInActiveBots += bot.channels_count || 0;
      }
    }
    
    // Возвращаем количество каналов в активных ботах
    // Это не идеально (может быть пересечение), но лучше чем показывать все каналы системы
    return totalChannelsInActiveBots;
  };

  // Загрузка статистики при монтировании
  useEffect(() => {
    loadStats();
    loadAIStats();
  }, []);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Заголовок страницы */}
      <Typography variant="h4" gutterBottom>
        📚 Posts Cache Monitor
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Мониторинг постов из Userbot и результатов AI обработки
      </Typography>

      {/* Общая статистика */}
      {stats && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Всего постов
                </Typography>
                <Typography variant="h5">
                  {stats.total_posts?.toLocaleString() || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Используется каналов
                </Typography>
                <Typography variant="h5">
                  {getUsedChannelsCount()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Размер данных
                </Typography>
                <Typography variant="h5">
                  {stats.total_size_mb ? `${stats.total_size_mb.toFixed(1)} MB` : 'N/A'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Последнее обновление
                </Typography>
                <Typography variant="h6">
                  {stats.last_updated ? new Date(stats.last_updated).toLocaleString('ru-RU') : 'N/A'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Ошибки */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Индикатор загрузки */}
      {loading && (
        <Box display="flex" justifyContent="center" sx={{ mb: 3 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Двухтабная архитектура */}
      <Paper sx={{ width: '100%' }}>
        {/* Заголовки табов */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={currentTab} 
            onChange={handleTabChange}
            aria-label="Posts Cache Monitor Tabs"
            variant="fullWidth"
          >
            <Tab 
              icon={<StorageIcon />}
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  <span>RAW POSTS</span>
                  <Chip 
                    label="Быстро" 
                    size="small" 
                    color="primary" 
                    variant="outlined"
                  />
                </Box>
              }
              iconPosition="start"
              sx={{ minHeight: 64 }}
            />
            <Tab 
              icon={<PsychologyIcon />}
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  <span>AI RESULTS</span>
                  <Chip 
                    label="Мультитенант" 
                    size="small" 
                    color="secondary" 
                    variant="outlined"
                  />
                </Box>
              }
              iconPosition="start"
              sx={{ minHeight: 64 }}
            />
          </Tabs>
        </Box>

        {/* Содержимое табов */}
        <Box sx={{ p: 3 }}>
          {currentTab === 0 && (
            <RawPostsTab 
              stats={stats}
              onStatsUpdate={loadStats}
            />
          )}
          
          {currentTab === 1 && (
            <AIResultsTab 
              stats={stats}
              onStatsUpdate={loadStats}
            />
          )}
        </Box>
      </Paper>
    </Box>
  );
}

export default PostsCachePage; 