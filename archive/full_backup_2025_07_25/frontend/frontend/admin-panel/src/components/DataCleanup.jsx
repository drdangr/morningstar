import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Alert,
  CircularProgress,
  Checkbox,
  FormControlLabel,
  Grid
} from '@mui/material';
import { Delete as DeleteIcon, Tv as ChannelIcon, SmartToy as BotIcon, Warning as WarningIcon } from '@mui/icons-material';

const DataCleanup = () => {
  const [channels, setChannels] = useState([]);
  const [bots, setBots] = useState([]);
  const [selectedChannel, setSelectedChannel] = useState('');
  const [selectedBot, setSelectedBot] = useState('');
  const [confirmDialog, setConfirmDialog] = useState(false);
  const [confirmData, setConfirmData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [cleanupType, setCleanupType] = useState('');
  const [cleanupOptions, setCleanupOptions] = useState({
    includePosts: false,      // ✅ ИСПРАВЛЕНО: по умолчанию НЕ удаляем посты
    includeAIResults: true    // ✅ По умолчанию удаляем только AI результаты
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      console.log('Загрузка данных...');
      
      const [channelsRes, botsRes] = await Promise.all([
        fetch('http://localhost:8000/api/channels'),
        fetch('http://localhost:8000/api/public-bots')
      ]);
      
      console.log('Ответ каналов:', channelsRes.status);
      console.log('Ответ ботов:', botsRes.status);
      
      if (channelsRes.ok) {
        const channelsData = await channelsRes.json();
        console.log('Данные каналов:', channelsData);
        setChannels(Array.isArray(channelsData) ? channelsData : []);
      } else {
        console.error('Ошибка загрузки каналов:', channelsRes.status);
        setMessage('❌ Ошибка загрузки каналов');
      }
      
      if (botsRes.ok) {
        const botsData = await botsRes.json();
        console.log('Данные ботов:', botsData);
        setBots(Array.isArray(botsData) ? botsData : []);
      } else {
        console.error('Ошибка загрузки ботов:', botsRes.status);
        setMessage('❌ Ошибка загрузки ботов');
      }
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
      setMessage(`❌ Ошибка загрузки данных: ${error.message}`);
    }
  };

  const showConfirm = (type) => {
    setCleanupType(type);
    
    let confirmText = '';
    switch (type) {
      case 'all':
        confirmText = 'Вы уверены, что хотите удалить ВСЕ данные из системы? Это действие необратимо!';
        break;
      case 'channel':
        if (!selectedChannel) {
          setMessage('❌ Выберите канал для очистки');
          return;
        }
        const channelName = channels.find(c => c.id === selectedChannel)?.channel_name || 'Неизвестный канал';
        confirmText = `Вы уверены, что хотите удалить все данные канала "${channelName}"? Это действие необратимо!`;
        break;
      case 'bot':
        if (!selectedBot) {
          setMessage('❌ Выберите бота для очистки');
          return;
        }
        const botName = bots.find(b => b.id === selectedBot)?.name || 'Неизвестный бот';
        confirmText = `Вы уверены, что хотите удалить все данные бота "${botName}"? Это действие необратимо!`;
        break;
      default:
        return;
    }
    
    setConfirmData({ text: confirmText });
    setConfirmDialog(true);
  };

  const executeCleanup = async () => {
    setLoading(true);
    setConfirmDialog(false);
    setMessage('');
    
    try {
      let url = '';
      const params = new URLSearchParams({
        confirm: 'true',
        include_posts: cleanupOptions.includePosts,
        include_ai_results: cleanupOptions.includeAIResults
      });

      switch (cleanupType) {
        case 'all':
          url = `http://localhost:8000/api/data/clear-all?${params}`;
          break;
        case 'channel':
          url = `http://localhost:8000/api/data/clear-by-channel/${selectedChannel}?${params}`;
          break;
        case 'bot':
          url = `http://localhost:8000/api/data/clear-by-bot/${selectedBot}?${params}`;
          break;
        default:
          throw new Error('Неизвестный тип очистки');
      }

      console.log('Отправка запроса на:', url);
      const response = await fetch(url, { method: 'DELETE' });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Неизвестная ошибка' }));
        throw new Error(errorData.message || `HTTP ${response.status}`);
      }
      
      const result = await response.json();
      setMessage(`✅ Успешно очищено: ${result.message}`);
      
      setSelectedChannel('');
      setSelectedBot('');
      
    } catch (error) {
      console.error('Ошибка очистки:', error);
      setMessage(`❌ Ошибка очистки: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        🧹 Мультитенантная очистка данных
      </Typography>

      {message && (
        <Alert severity={message.includes('❌') ? 'error' : 'success'} sx={{ mb: 2 }}>
          {message}
        </Alert>
      )}

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            ⚙️ Настройки очистки
          </Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Рекомендуется:</strong> Очищать только AI результаты и сбрасывать статус на "pending". 
              Удаление постов приведет к потере исходных данных!
            </Typography>
          </Alert>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={cleanupOptions.includePosts}
                  onChange={(e) => setCleanupOptions(prev => ({ ...prev, includePosts: e.target.checked }))}
                />
              }
              label="⚠️ Удалить посты (ОПАСНО!)"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={cleanupOptions.includeAIResults}
                  onChange={(e) => setCleanupOptions(prev => ({ ...prev, includeAIResults: e.target.checked }))}
                />
              }
              label="✅ Очистить AI результаты (рекомендуется)"
            />
          </Box>
          <Typography variant="caption" color="text.secondary">
            Загружено: {channels.length} каналов, {bots.length} ботов
          </Typography>
        </CardContent>
      </Card>

      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="error" gutterBottom>
                <DeleteIcon sx={{ mr: 1 }} />
                Полная очистка
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                По умолчанию: очищает AI результаты и сбрасывает статус на "pending"
              </Typography>
              <Button
                variant="contained"
                color="error"
                fullWidth
                disabled={loading}
                onClick={() => showConfirm('all')}
                startIcon={<DeleteIcon />}
              >
                {loading && cleanupType === 'all' ? 'Очистка...' : 'Очистить все данные'}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <ChannelIcon sx={{ mr: 1 }} />
                Очистка по каналу
              </Typography>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Выберите канал</InputLabel>
                <Select
                  value={selectedChannel}
                  onChange={(e) => setSelectedChannel(e.target.value)}
                  label="Выберите канал"
                >
                  {channels.map((channel) => (
                    <MenuItem key={channel.id} value={channel.id}>
                      {channel.channel_name} (@{channel.username})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Button
                variant="contained"
                color="warning"
                fullWidth
                disabled={loading || !selectedChannel}
                onClick={() => showConfirm('channel')}
                startIcon={<DeleteIcon />}
              >
                {loading && cleanupType === 'channel' ? 'Очистка...' : 'Очистить канал'}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <BotIcon sx={{ mr: 1 }} />
                Очистка по боту
              </Typography>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Выберите бота</InputLabel>
                <Select
                  value={selectedBot}
                  onChange={(e) => setSelectedBot(e.target.value)}
                  label="Выберите бота"
                >
                  {bots.map((bot) => (
                    <MenuItem key={bot.id} value={bot.id}>
                      {bot.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Button
                variant="contained"
                color="warning"
                fullWidth
                disabled={loading || !selectedBot}
                onClick={() => showConfirm('bot')}
                startIcon={<DeleteIcon />}
              >
                {loading && cleanupType === 'bot' ? 'Очистка...' : 'Очистить бота'}
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={confirmDialog} onClose={() => setConfirmDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <WarningIcon color="warning" sx={{ mr: 1 }} />
          Подтверждение очистки данных
        </DialogTitle>
        <DialogContent>
          {confirmData && (
            <Box>
              <Typography variant="body1" gutterBottom>
                {confirmData.text}
              </Typography>
              
              <Alert severity="warning" sx={{ mt: 2 }}>
                ⚠️ Это действие необратимо! Убедитесь, что вы хотите удалить эти данные.
              </Alert>
              
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Будет удалено:
                </Typography>
                <Typography variant="body2">
                  • {cleanupOptions.includePosts ? '✅' : '❌'} Посты из кэша
                </Typography>
                <Typography variant="body2">
                  • {cleanupOptions.includeAIResults ? '✅' : '❌'} AI результаты обработки
                </Typography>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog(false)}>
            Отмена
          </Button>
          <Button 
            onClick={executeCleanup} 
            color="error" 
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : <DeleteIcon />}
          >
            {loading ? 'Очистка...' : 'Подтвердить очистку'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DataCleanup; 