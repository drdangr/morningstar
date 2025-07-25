import React, { useState, useEffect } from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Chip,
  Grid,
  Paper,
  Divider
} from '@mui/material';
import { SmartToy, CheckCircle, Schedule, Error } from '@mui/icons-material';

const BotSelector = ({ selectedBot, onBotChange, aiStats }) => {
  const [botChannels, setBotChannels] = useState([]);
  const [botCategories, setBotCategories] = useState([]);
  const [loading, setLoading] = useState(false);

  // Получаем данные выбранного бота из AI stats
  const selectedBotStats = aiStats?.bots_stats?.find(bot => bot.bot_id === selectedBot);

  // Загружаем каналы и категории выбранного бота
  useEffect(() => {
    if (selectedBot) {
      loadBotDetails(selectedBot);
    }
  }, [selectedBot]);

  const loadBotDetails = async (botId) => {
    setLoading(true);
    try {
      // Загружаем каналы бота
      const channelsResponse = await fetch(`http://localhost:8000/api/public-bots/${botId}/channels`);
      if (channelsResponse.ok) {
        const channels = await channelsResponse.json();
        setBotChannels(channels);
      }

      // Загружаем категории бота
      const categoriesResponse = await fetch(`http://localhost:8000/api/public-bots/${botId}/categories`);
      if (categoriesResponse.ok) {
        const categories = await categoriesResponse.json();
        setBotCategories(categories.filter(cat => cat.category_name && cat.category_name !== 'None'));
      }
    } catch (error) {
      console.error('Error loading bot details:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <CheckCircle />;
      case 'inactive': return <Schedule />;
      case 'error': return <Error />;
      default: return <SmartToy />;
    }
  };

  if (!aiStats?.bots_stats?.length) {
    return (
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          <SmartToy sx={{ mr: 1, verticalAlign: 'middle' }} />
          Выбор бота для мультитенантной фильтрации
        </Typography>
        <Typography color="text.secondary">
          Нет доступных ботов для отображения AI результатов.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        <SmartToy sx={{ mr: 1, verticalAlign: 'middle' }} />
        Выбор бота для мультитенантной фильтрации
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Каждый бот имеет свои индивидуальные AI результаты. Выберите бота для просмотра его обработанных постов.
      </Typography>

      {/* Селектор бота */}
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Выберите бота</InputLabel>
        <Select
          value={selectedBot || ''}
          onChange={(e) => onBotChange(e.target.value)}
          label="Выберите бота"
        >
          {aiStats.bots_stats.map((bot) => (
            <MenuItem key={bot.bot_id} value={bot.bot_id}>
              <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                {getStatusIcon(bot.status)}
                <Typography sx={{ ml: 1, flexGrow: 1 }}>
                  {bot.name}
                </Typography>
                <Chip
                  label={bot.status}
                  color={getStatusColor(bot.status)}
                  size="small"
                />
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Статистика выбранного бота */}
      {selectedBotStats && (
        <Box>
          <Divider sx={{ my: 2 }} />
          
          {/* Первая строка: AI статистика */}
          <Box sx={{ mb: 2 }}>
            <Grid container spacing={1}>
              <Grid item>
                <Chip 
                  label={`${selectedBotStats.multitenant_stats.categorized} категоризировано`} 
                  color="success" 
                  size="small" 
                />
              </Grid>
              <Grid item>
                <Chip 
                  label={`${selectedBotStats.multitenant_stats.summarized} саммаризировано`} 
                  color="info" 
                  size="small" 
                />
              </Grid>
              <Grid item>
                <Chip 
                  label={`${selectedBotStats.multitenant_stats.processing} в обработке`} 
                  color="warning" 
                  size="small" 
                />
              </Grid>
            </Grid>
          </Box>

          {/* Вторая строка: каналы и темы */}
          <Box>
            <Grid container spacing={1}>
              {/* Каналы */}
              {botChannels.map((channel, index) => (
                <Grid item key={`channel-${index}`}>
                  <Chip 
                    label={channel.username} 
                    variant="outlined" 
                    size="small"
                    color="primary"
                  />
                </Grid>
              ))}
              
              {/* Темы */}
              {botCategories.map((category, index) => (
                <Grid item key={`category-${index}`}>
                  <Chip 
                    label={category.category_name} 
                    variant="outlined" 
                    size="small"
                    color="secondary"
                  />
                </Grid>
              ))}
              
              {/* Показываем если данные загружаются */}
              {loading && (
                <Grid item>
                  <Chip 
                    label="Загрузка..." 
                    variant="outlined" 
                    size="small"
                  />
                </Grid>
              )}
              
              {/* Показываем если нет каналов/категорий */}
              {!loading && botChannels.length === 0 && (
                <Grid item>
                  <Chip 
                    label="Нет каналов" 
                    variant="outlined" 
                    size="small"
                    color="default"
                  />
                </Grid>
              )}
              
              {!loading && botCategories.length === 0 && (
                <Grid item>
                  <Chip 
                    label="Нет тем" 
                    variant="outlined" 
                    size="small"
                    color="default"
                  />
                </Grid>
              )}
            </Grid>
          </Box>
        </Box>
      )}

      {/* Общая статистика */}
      <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
        <Typography variant="body2" color="text.secondary">
          Доступные боты: {aiStats.bots_stats.length} | Активных: {aiStats.bots_stats.filter(b => b.status === 'active').length} | На паузе: {aiStats.bots_stats.filter(b => b.status === 'inactive').length} | В настройке: 1
        </Typography>
      </Box>
    </Paper>
  );
};

export default BotSelector; 