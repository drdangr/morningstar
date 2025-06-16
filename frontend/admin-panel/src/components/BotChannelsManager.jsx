import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Checkbox,
  FormControlLabel,
  TextField,
  Chip,
  Card,
  CardContent,
  Grid,
  Alert,
  Divider,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  CircularProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Remove as RemoveIcon,
  Search as SearchIcon,
  FileUpload as ImportIcon,
  FileDownload as ExportIcon,
  Sync as SyncIcon,
  CheckBox as BulkIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';

const BotChannelsManager = ({ botId, botChannels, onChannelsChange }) => {
  const [availableChannels, setAvailableChannels] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [bulkDialogOpen, setBulkDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Загрузка доступных каналов
  useEffect(() => {
    loadAvailableChannels();
  }, [botId, botChannels]);

  const loadAvailableChannels = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/channels');
      if (!response.ok) throw new Error('Ошибка загрузки каналов');
      
      const channels = await response.json();
      
      // Фильтруем каналы, которые еще не добавлены к боту
      const botChannelIds = (botChannels || []).map(ch => ch.id);
      const available = channels.filter(ch => !botChannelIds.includes(ch.id));
      
      setAvailableChannels(available);
      setError('');
    } catch (error) {
      console.error('Ошибка загрузки каналов:', error);
      setError('Ошибка загрузки каналов: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Фильтрация каналов по поиску
  const filteredChannels = availableChannels.filter(channel =>
    (channel.channel_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (channel.username || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (channel.title || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Обработка выбора каналов
  const handleChannelSelect = (channelId, selected) => {
    if (selected) {
      setSelectedChannels([...selectedChannels, channelId]);
    } else {
      setSelectedChannels(selectedChannels.filter(id => id !== channelId));
    }
  };

  // Выбрать все отфильтрованные каналы
  const handleSelectAll = () => {
    const allIds = filteredChannels.map(ch => ch.id);
    setSelectedChannels(allIds);
  };

  // Очистить выбор
  const handleClearSelection = () => {
    setSelectedChannels([]);
  };

  // Bulk добавление выбранных каналов
  const handleBulkAdd = async () => {
    if (selectedChannels.length === 0) return;

    setLoading(true);
    try {
      // Используем реальный API для добавления каналов к боту
      const response = await fetch(`http://localhost:8000/api/public-bots/${botId}/channels`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          channel_ids: selectedChannels
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка добавления каналов');
      }

      // Получаем обновленный список каналов бота
      const botChannelsResponse = await fetch(`http://localhost:8000/api/public-bots/${botId}/channels`);
      if (botChannelsResponse.ok) {
        const updatedBotChannels = await botChannelsResponse.json();
        onChannelsChange(updatedBotChannels);
      }
      
      // Очищаем выбор
      setSelectedChannels([]);
      setError('');
      
    } catch (error) {
      console.error('Ошибка добавления каналов:', error);
      setError('Ошибка добавления каналов: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Удаление канала из бота
  const handleRemoveChannel = async (channelId) => {
    try {
      // Используем реальный API для удаления канала из бота
      const response = await fetch(`http://localhost:8000/api/public-bots/${botId}/channels/${channelId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка удаления канала');
      }

      // Получаем обновленный список каналов бота
      const botChannelsResponse = await fetch(`http://localhost:8000/api/public-bots/${botId}/channels`);
      if (botChannelsResponse.ok) {
        const updatedBotChannels = await botChannelsResponse.json();
        onChannelsChange(updatedBotChannels);
      }
      
      setError('');
      
    } catch (error) {
      console.error('Ошибка удаления канала:', error);
      setError('Ошибка удаления канала: ' + error.message);
    }
  };

  // Экспорт каналов в CSV
  const handleExport = () => {
    const csvContent = [
      'ID,Название,Username,Описание,Telegram ID',
      ...(botChannels || []).map(ch => 
        `${ch.id},"${ch.title || ch.channel_name}","${ch.username || ''}","${ch.description || ''}",${ch.telegram_id || ''}`
      )
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bot_${botId}_channels.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Header с поиском и bulk действиями */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, flexWrap: 'wrap', gap: 2 }}>
        <TextField
          placeholder="Поиск каналов..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
          }}
          sx={{ minWidth: 300 }}
        />
        
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button
            variant="outlined"
            startIcon={<ExportIcon />}
            onClick={handleExport}
            disabled={(botChannels || []).length === 0}
          >
            Экспорт
          </Button>
          <Button
            variant="outlined"
            startIcon={<SyncIcon />}
            onClick={loadAvailableChannels}
            disabled={loading}
          >
            Обновить
          </Button>
        </Box>
      </Box>

      {/* Статистика */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="primary" component="div">
                {(botChannels || []).length}
              </Typography>
              <Typography variant="body2" color="text.secondary" component="div">
                Добавленные каналы
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="secondary" component="div">
                {availableChannels.length}
              </Typography>
              <Typography variant="body2" color="text.secondary" component="div">
                Доступные каналы
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="info.main" component="div">
                {selectedChannels.length}
              </Typography>
              <Typography variant="body2" color="text.secondary" component="div">
                Выбрано
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary" component="div">
                {filteredChannels.length}
              </Typography>
              <Typography variant="body2" color="text.secondary" component="div">
                По фильтру
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Добавленные каналы */}
      {(botChannels || []).length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Добавленные каналы ({(botChannels || []).length})
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {(botChannels || []).map(channel => (
              <Chip 
                key={channel.id}
                label={channel.title || channel.channel_name}
                onDelete={() => handleRemoveChannel(channel.id)}
                color="primary"
                variant="outlined"
              />
            ))}
          </Box>
        </Box>
      )}

      <Divider sx={{ my: 2 }} />

      {/* Bulk selection controls */}
      {availableChannels.length > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button size="small" onClick={handleSelectAll}>
              Выбрать все ({filteredChannels.length})
            </Button>
            <Button size="small" onClick={handleClearSelection}>
              Очистить выбор
            </Button>
          </Box>
          
          {selectedChannels.length > 0 && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleBulkAdd}
              disabled={loading}
            >
              Добавить выбранные ({selectedChannels.length})
            </Button>
          )}
        </Box>
      )}

      {/* Список доступных каналов */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : (
        <List>
          {filteredChannels.map(channel => (
            <ListItem key={channel.id} divider>
              <ListItemIcon>
                <Checkbox
                  checked={selectedChannels.includes(channel.id)}
                  onChange={(e) => handleChannelSelect(channel.id, e.target.checked)}
                />
              </ListItemIcon>
              <Box sx={{ flex: 1, ml: 2 }}>
                <Typography variant="body1" component="div">
                  {channel.title || channel.channel_name}
                </Typography>
                <Typography variant="body2" color="text.secondary" component="div">
                  @{channel.username || 'Нет username'} • ID: {channel.telegram_id}
                </Typography>
                {channel.description && (
                  <Typography variant="body2" color="text.secondary" component="div" sx={{ mt: 0.5 }}>
                    {channel.description}
                  </Typography>
                )}
              </Box>
              <ListItemSecondaryAction>
                <IconButton
                  edge="end"
                  onClick={() => handleChannelSelect(channel.id, !selectedChannels.includes(channel.id))}
                >
                  {selectedChannels.includes(channel.id) ? <RemoveIcon /> : <AddIcon />}
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      )}

      {filteredChannels.length === 0 && !loading && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body1" color="text.secondary">
            {searchTerm ? 'Каналы не найдены по запросу' : 'Все доступные каналы уже добавлены'}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default BotChannelsManager; 