import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  Button,
  Alert,
  Card,
  CardContent,
  Grid,
  Chip,
  IconButton,
  Tooltip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  InputAdornment
} from '@mui/material';
import {
  Add as AddIcon,
  Settings as SettingsIcon,
  Visibility as PreviewIcon,
  PlayArrow as StartIcon,
  Pause as PauseIcon,
  AccessTime as TimeIcon,
  Language as LanguageIcon,
  Message as MessageIcon
} from '@mui/icons-material';

// Импорт bulk операций из temp
import BotConfigurationTabs from '../components/BotConfigurationTabs';

const API_BASE_URL = 'http://localhost:8000';

function PublicBotsPage() {
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [selectedBot, setSelectedBot] = useState(null);
  const [originalBot, setOriginalBot] = useState(null);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    bot_token: '',
    welcome_message: '',
    default_language: 'ru',
    max_posts_per_digest: 10,
    max_summary_length: 150,
    categorization_prompt: '',
    summarization_prompt: '',
    delivery_schedule: {},
    timezone: 'Europe/Moscow'
  });

  // Загрузка ботов из API
  const loadBots = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/public-bots`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setBots(data);
    } catch (err) {
      setError('Ошибка загрузки ботов: ' + err.message);
      console.error('Error loading bots:', err);
    } finally {
      setLoading(false);
    }
  };

  // Создание нового бота
  const handleCreateBot = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/public-bots`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      await loadBots();
      setCreateDialogOpen(false);
      setFormData({
        name: '',
        description: '',
        bot_token: '',
        welcome_message: '',
        default_language: 'ru',
        max_posts_per_digest: 10,
        max_summary_length: 150,
        categorization_prompt: '',
        summarization_prompt: '',
        delivery_schedule: {},
        timezone: 'Europe/Moscow'
      });
    } catch (err) {
      setError('Ошибка создания бота: ' + err.message);
      console.error('Error creating bot:', err);
    }
  };

  // Обновление настроек бота
  const handleUpdateBot = async (updatedBot) => {
    setSaving(true);
    setError('');
    
    try {
      console.log('🔄 Обновляем настройки бота:', updatedBot.id);
      
      const response = await fetch(`${API_BASE_URL}/api/public-bots/${updatedBot.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: updatedBot.name,
          description: updatedBot.description,
          bot_token: updatedBot.bot_token,
          welcome_message: updatedBot.welcome_message,
          default_language: updatedBot.default_language,
          max_posts_per_digest: updatedBot.max_posts_per_digest,
          max_summary_length: updatedBot.max_summary_length,
          categorization_prompt: updatedBot.categorization_prompt,
          summarization_prompt: updatedBot.summarization_prompt,
          delivery_schedule: updatedBot.delivery_schedule,
          timezone: updatedBot.timezone
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const updatedBotData = await response.json();
      console.log('✅ Настройки бота обновлены:', updatedBotData);
      
      // Обновляем selectedBot для отображения изменений
      setSelectedBot(updatedBotData);
      
      // Обновляем originalBot чтобы сбросить индикатор изменений
      setOriginalBot(JSON.parse(JSON.stringify(updatedBotData)));
      
      // Перезагружаем список ботов
      await loadBots();
      
    } catch (err) {
      setError('Ошибка обновления настроек: ' + err.message);
      console.error('Error updating bot:', err);
    } finally {
      setSaving(false);
    }
  };

  // Переключение статуса бота
  const toggleBotStatus = async (botId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/public-bots/${botId}/toggle-status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      await loadBots();
    } catch (err) {
      setError('Ошибка изменения статуса: ' + err.message);
      console.error('Error toggling status:', err);
    }
  };

  // Проверка наличия изменений
  const hasChanges = () => {
    if (!selectedBot || !originalBot) return false;
    return JSON.stringify(selectedBot) !== JSON.stringify(originalBot);
  };

  useEffect(() => {
    loadBots();
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'setup': return 'warning';
      case 'paused': return 'error';
      default: return 'default';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'active': return 'Активен';
      case 'setup': return 'Настройка';
      case 'paused': return 'Пауза';
      default: return 'Неизвестно';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          🤖 Public Bots Management
        </Typography>
        
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
          sx={{ ml: 1 }}
        >
          Создать бота
        </Button>
      </Box>

      {/* Overview Stats */}
      <Card sx={{ mb: 3, bgcolor: 'background.default' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            📊 Обзор
          </Typography>
          <Box sx={{ display: 'flex', gap: 3 }}>
            <Chip 
              label={`${bots.filter(b => b.status === 'active').length} активных`} 
              color="success" 
              variant="outlined"
            />
            <Chip 
              label={`${bots.filter(b => b.status === 'setup').length} в разработке`} 
              color="warning" 
              variant="outlined"
            />
            <Chip 
              label={`${bots.filter(b => b.status === 'paused').length} приостановлены`} 
              color="error" 
              variant="outlined"
            />
          </Box>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Loading */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Bots Grid */}
      {!loading && (
        <Grid container spacing={3}>
          {bots.map((bot) => (
            <Grid item xs={12} sm={6} md={4} key={bot.id}>
              <Card 
                sx={{ 
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  bgcolor: 'background.default',
                  '&:hover': {
                    boxShadow: 4,
                    transform: 'translateY(-2px)',
                    transition: 'all 0.2s ease-in-out'
                  }
                }}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  {/* Bot Header */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
                      {bot.name}
                    </Typography>
                    <Chip 
                      label={getStatusText(bot.status)}
                      color={getStatusColor(bot.status)}
                      size="small"
                    />
                  </Box>

                  {/* Bot Description */}
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {bot.description || 'Описание не указано'}
                  </Typography>

                  {/* Bot Stats */}
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LanguageIcon fontSize="small" color="action" />
                      <Typography variant="body2">
                        {bot.default_language.toUpperCase()}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <TimeIcon fontSize="small" color="action" />
                      <Typography variant="body2">
                        {bot.digest_generation_time} • {bot.max_posts_per_digest} постов
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <MessageIcon fontSize="small" color="action" />
                      <Typography variant="body2">
                        {bot.max_summary_length} симв. • {bot.users_count} пользователей
                      </Typography>
                    </Box>
                  </Box>

                  {/* AI Prompt Preview */}
                  {bot.ai_prompt && (
                    <Box sx={{ mt: 2, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        AI Prompt:
                      </Typography>
                      <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                        {bot.ai_prompt.length > 100 ? `${bot.ai_prompt.substring(0, 100)}...` : bot.ai_prompt}
                      </Typography>
                    </Box>
                  )}
                </CardContent>

                {/* Bot Actions */}
                <Box sx={{ p: 2, pt: 0, display: 'flex', justifyContent: 'space-between', borderTop: 1, borderColor: 'divider' }}>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Tooltip title="Настройки бота">
                      <IconButton 
                        size="small" 
                        onClick={() => {
                          setSelectedBot(bot);
                          setOriginalBot(JSON.parse(JSON.stringify(bot))); // Глубокая копия
                          setSettingsDialogOpen(true);
                        }}
                      >
                        <SettingsIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Превью дайджеста">
                      <IconButton 
                        size="small"
                        onClick={() => {
                          setSelectedBot(bot);
                          setPreviewDialogOpen(true);
                        }}
                      >
                        <PreviewIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                  
                  <Tooltip title={bot.status === 'active' ? 'Приостановить' : 'Запустить'}>
                    <IconButton 
                      size="small"
                      color={bot.status === 'active' ? 'error' : 'success'}
                      onClick={() => toggleBotStatus(bot.id)}
                    >
                      {bot.status === 'active' ? <PauseIcon /> : <StartIcon />}
                    </IconButton>
                  </Tooltip>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Empty State */}
      {!loading && bots.length === 0 && !error && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Публичные боты не найдены
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Создайте первого бота для начала работы
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Создать первого бота
          </Button>
        </Box>
      )}

      {/* Create Bot Dialog */}
      <Dialog 
        open={createDialogOpen} 
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Создать нового бота</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Название бота"
              fullWidth
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
            <TextField
              label="Описание"
              fullWidth
              multiline
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
            <TextField
              label="Telegram Bot Token"
              fullWidth
              value={formData.bot_token}
              onChange={(e) => setFormData({ ...formData, bot_token: e.target.value })}
              required
            />
            <TextField
              label="Приветственное сообщение"
              fullWidth
              multiline
              rows={2}
              value={formData.welcome_message}
              onChange={(e) => setFormData({ ...formData, welcome_message: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>Язык по умолчанию</InputLabel>
              <Select
                value={formData.default_language}
                onChange={(e) => setFormData({ ...formData, default_language: e.target.value })}
                label="Язык по умолчанию"
              >
                <MenuItem value="ru">Русский</MenuItem>
                <MenuItem value="en">English</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Максимум постов в дайджесте"
              type="number"
              fullWidth
              value={formData.max_posts_per_digest}
              onChange={(e) => setFormData({ ...formData, max_posts_per_digest: parseInt(e.target.value) })}
              InputProps={{
                startAdornment: <InputAdornment position="start">📝</InputAdornment>,
              }}
            />
            <TextField
              label="Максимальная длина резюме"
              type="number"
              fullWidth
              value={formData.max_summary_length}
              onChange={(e) => setFormData({ ...formData, max_summary_length: parseInt(e.target.value) })}
              InputProps={{
                startAdornment: <InputAdornment position="start">📏</InputAdornment>,
              }}
            />
            <TextField
              label="Промпт для категоризации"
              fullWidth
              multiline
              rows={3}
              value={formData.categorization_prompt}
              onChange={(e) => setFormData({ ...formData, categorization_prompt: e.target.value })}
            />
            <TextField
              label="Промпт для суммаризации"
              fullWidth
              multiline
              rows={3}
              value={formData.summarization_prompt}
              onChange={(e) => setFormData({ ...formData, summarization_prompt: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Отмена</Button>
          <Button 
            onClick={handleCreateBot} 
            variant="contained"
            disabled={!formData.name || !formData.bot_token}
          >
            Создать
          </Button>
        </DialogActions>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog
        open={settingsDialogOpen}
        onClose={() => {
          if (hasChanges()) {
            if (window.confirm('У вас есть несохраненные изменения. Закрыть без сохранения?')) {
              setSelectedBot(originalBot); // Восстанавливаем оригинальные данные
              setSettingsDialogOpen(false);
            }
          } else {
            setSettingsDialogOpen(false);
          }
        }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            Настройки бота {selectedBot?.name}
            {hasChanges() && (
              <Chip 
                label="Есть изменения" 
                color="warning" 
                size="small" 
                variant="outlined"
              />
            )}
          </Box>
        </DialogTitle>
        <DialogContent>
          <BotConfigurationTabs 
            bot={selectedBot} 
            onBotUpdate={(updatedBot) => setSelectedBot(updatedBot)}
            onClose={() => setSettingsDialogOpen(false)}
          />
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => {
              setSelectedBot(originalBot); // Восстанавливаем оригинальные данные
              setSettingsDialogOpen(false);
            }}
          >
            Отмена
          </Button>
          <Button 
            variant="contained" 
            disabled={!hasChanges() || saving}
            onClick={() => {
              if (selectedBot) {
                handleUpdateBot(selectedBot);
              }
            }}
            startIcon={saving ? <CircularProgress size={16} /> : null}
          >
            {saving ? 'Сохранение...' : 'Сохранить изменения'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Preview Dialog */}
      <Dialog
        open={previewDialogOpen}
        onClose={() => setPreviewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Превью дайджеста {selectedBot?.name}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary">
            Превью дайджеста будет доступно в Task 3
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialogOpen(false)}>Закрыть</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default PublicBotsPage; 