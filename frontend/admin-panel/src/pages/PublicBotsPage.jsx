import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  Grid,
  IconButton,
  InputAdornment,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
  Alert
} from '@mui/material';
import {
  Add as AddIcon,
  Settings as SettingsIcon,
  Visibility as PreviewIcon,
  PlayArrow as StartIcon,
  Pause as PauseIcon,
  AccessTime as TimeIcon,
  Language as LanguageIcon,
  Message as MessageIcon,
  Delete as DeleteIcon,
  Folder as CategoryIcon,
  Tv as ChannelIcon
} from '@mui/icons-material';

// Импорт bulk операций из temp
import BotConfigurationTabs from '../components/BotConfigurationTabs';
import { apiEndpoints, API_BASE_URL } from '../config/api';

function PublicBotsPage() {
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedBot, setSelectedBot] = useState(null);
  const [originalBot, setOriginalBot] = useState(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [botSubscriptions, setBotSubscriptions] = useState({});
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
    digest_schedule: {"enabled": false},
    timezone: 'Europe/Moscow'
  });

  // Загрузка ботов из API
  const loadBots = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(apiEndpoints.publicBots());
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setBots(data);
    } catch (err) {
      console.error('Ошибка загрузки ботов:', err);
      setError('Не удалось загрузить список ботов');
    } finally {
      setLoading(false);
    }
  };

  // Загрузка подписок для всех ботов
  const loadBotSubscriptions = async (botsArray = bots) => {
    try {
      // Проверяем что боты загружены
      if (!botsArray || botsArray.length === 0) {
        console.log('Боты еще не загружены, пропускаем загрузку подписок');
        return;
      }

      const subscriptionsData = {};
      
      // Загружаем подписки для каждого бота параллельно
      const subscriptionPromises = botsArray.map(async (bot) => {
        try {
          // Загружаем каналы бота
          const channelsResponse = await fetch(apiEndpoints.botChannels(bot.id));
          const channels = channelsResponse.ok ? await channelsResponse.json() : [];
          
          // Загружаем категории бота
          const categoriesResponse = await fetch(apiEndpoints.botCategories(bot.id));
          const categories = categoriesResponse.ok ? await categoriesResponse.json() : [];
          
          subscriptionsData[bot.id] = {
            channels: channels,
            categories: categories
          };
        } catch (err) {
          console.error(`Ошибка загрузки подписок для бота ${bot.id}:`, err);
          subscriptionsData[bot.id] = {
            channels: [],
            categories: []
          };
        }
      });
      
      await Promise.all(subscriptionPromises);
      setBotSubscriptions(subscriptionsData);
      console.log('✅ Подписки ботов загружены:', subscriptionsData);
    } catch (err) {
      console.error('Ошибка загрузки подписок:', err);
    }
  };

  // Заполнение формы дефолтными значениями
  const handleFillDefaults = async () => {
    try {
      console.log('🎯 LOADING DEFAULTS - загружаем дефолтные настройки...');
      
      const response = await fetch(apiEndpoints.botTemplates());
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const defaults = await response.json();
      console.log('🎯 LOADING DEFAULTS - получены дефолтные настройки:', defaults);

      // Заполняем форму дефолтными значениями (сохраняя уже заполненные поля)
      setFormData(prevData => ({
        ...prevData,
        welcome_message: defaults.default_welcome_message || prevData.welcome_message,
        default_language: defaults.default_digest_language || prevData.default_language,
        max_posts_per_digest: defaults.default_max_posts_per_digest || prevData.max_posts_per_digest,
        max_summary_length: defaults.default_max_summary_length || prevData.max_summary_length,
        categorization_prompt: defaults.default_categorization_prompt || prevData.categorization_prompt,
        summarization_prompt: defaults.default_summarization_prompt || prevData.summarization_prompt,
        delivery_schedule: defaults.default_delivery_schedule || prevData.delivery_schedule,
        digest_schedule: defaults.default_digest_schedule || prevData.digest_schedule,
        timezone: defaults.default_timezone || prevData.timezone
      }));

      console.log('🎯 LOADING DEFAULTS - форма заполнена дефолтными значениями');
    } catch (err) {
      setError('Ошибка загрузки дефолтных настроек: ' + err.message);
      console.error('🎯 LOADING DEFAULTS - Error loading defaults:', err);
    }
  };

  // Создание нового бота
  const handleCreateBot = async () => {
    try {
      console.log('🎯 CREATING BOT - formData перед отправкой:', formData);
      console.log('🎯 CREATING BOT - formData as JSON:', JSON.stringify(formData, null, 2));
      console.log('🎯 CREATING BOT - URL:', apiEndpoints.publicBots());
      
      const response = await fetch(apiEndpoints.publicBots(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      console.log('🎯 CREATING BOT - response status:', response.status);
      console.log('🎯 CREATING BOT - response ok:', response.ok);

      if (!response.ok) {
        const errorData = await response.text();
        console.log('🎯 CREATING BOT - error response:', errorData);
        throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorData}`);
      }

      const responseData = await response.json();
      console.log('🎯 CREATING BOT - success response:', responseData);

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
        digest_schedule: {"enabled": false},
        timezone: 'Europe/Moscow'
      });
    } catch (err) {
      setError('Ошибка создания бота: ' + err.message);
      console.error('🎯 CREATING BOT - Error creating bot:', err);
    }
  };

  // Обновление настроек бота
  const handleUpdateBot = async (updatedBot) => {
    setSaving(true);
    setError('');
    
    try {
      console.log('🔄 Обновляем настройки бота:', updatedBot.id);
      
      const response = await fetch(apiEndpoints.publicBot(updatedBot.id), {
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

      if (response.ok) {
        const result = await response.json();
        console.log('Status toggled:', result);
        await loadBots(); // Перезагружаем список ботов
      } else {
        throw new Error('Failed to toggle bot status');
      }
    } catch (error) {
      console.error('Error toggling bot status:', error);
      setError('Ошибка изменения статуса бота');
    }
  };

  const setBotStatus = async (botId, newStatus) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/public-bots/${botId}/set-status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Status set:', result);
        await loadBots(); // Перезагружаем список ботов
      } else {
        throw new Error('Failed to set bot status');
      }
    } catch (error) {
      console.error('Error setting bot status:', error);
      setError('Ошибка установки статуса бота');
    }
  };

  // Проверка наличия изменений
  const hasChanges = () => {
    if (!selectedBot || !originalBot) return false;
    return JSON.stringify(selectedBot) !== JSON.stringify(originalBot);
  };

  // Удаление бота
  const handleDeleteBot = async () => {
    if (!selectedBot) return;
    
    setDeleting(true);
    setError('');
    
    try {
      console.log('🗑️ Удаляем бота:', selectedBot.id);
      
      const response = await fetch(`${API_BASE_URL}/api/public-bots/${selectedBot.id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('✅ Бот удален:', result);
      
      // Перезагружаем список ботов
      await loadBots();
      
      // Закрываем диалог
      setDeleteDialogOpen(false);
      setSelectedBot(null);
      
    } catch (err) {
      setError('Ошибка удаления бота: ' + err.message);
      console.error('Error deleting bot:', err);
    } finally {
      setDeleting(false);
    }
  };

  // Генерация превью дайджеста
  const handleGeneratePreview = async (bot) => {
    setSelectedBot(bot);
    setPreviewDialogOpen(true);
    setPreviewLoading(true);
    setPreviewData(null);
    
    try {
      console.log('🔍 Генерируем превью дайджеста для бота:', bot.id);
      
      const response = await fetch(`${API_BASE_URL}/api/public-bots/${bot.id}/preview-digest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('✅ Превью дайджеста получен:', result);
      
      setPreviewData(result);
      
    } catch (err) {
      setError('Ошибка генерации превью: ' + err.message);
      console.error('Error generating preview:', err);
      
      // Устанавливаем fallback данные при ошибке
      setPreviewData({
        success: false,
        error: err.message,
        fallback_data: {
          bot_name: bot.name,
          message: "Не удалось сгенерировать превью дайджеста"
        }
      });
    } finally {
      setPreviewLoading(false);
    }
  };

  useEffect(() => {
    loadBots();
  }, []);

  // Загружаем подписки после загрузки ботов
  useEffect(() => {
    if (bots.length > 0) {
      loadBotSubscriptions(bots);
    }
  }, [bots.length]); // Зависимость только от длины массива

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'setup': return 'warning';
      case 'paused': return 'error';
      case 'development': return 'info';
      default: return 'default';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'active': return 'Активен';
      case 'setup': return 'Настройка';
      case 'paused': return 'Пауза';
      case 'development': return 'В разработке';
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
            Статистика ботов
          </Typography>
          <Box sx={{ display: 'flex', gap: 3 }}>
            <Chip 
              label={`${bots.filter(b => b.status === 'active').length} активных`} 
              color="success" 
              variant="outlined"
            />
            <Chip 
              label={`${bots.filter(b => b.status === 'setup').length} в настройке`} 
              color="warning" 
              variant="outlined"
            />
            <Chip 
              label={`${bots.filter(b => b.status === 'development').length} в разработке`} 
              color="info" 
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
                  position: 'relative',
                  '&:hover': {
                    boxShadow: 4,
                    transform: 'translateY(-2px)',
                    transition: 'all 0.2s ease-in-out'
                  }
                }}
              >
                {/* Delete Button - Top Right Corner */}
                <Tooltip title="Удалить бота">
                  <IconButton 
                    size="small"
                    color="error"
                    onClick={() => {
                      setSelectedBot(bot);
                      setDeleteDialogOpen(true);
                    }}
                    sx={{ 
                      position: 'absolute', 
                      top: 8, 
                      right: 8, 
                      zIndex: 1,
                      bgcolor: 'background.paper',
                      '&:hover': {
                        bgcolor: 'error.light',
                        color: 'white'
                      }
                    }}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Tooltip>

                <CardContent sx={{ flexGrow: 1 }}>
                  {/* Bot Header */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2, pr: 5 }}>
                    <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
                      {bot.name}
                    </Typography>
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
                    
                    {/* Bot Subscriptions */}
                    {botSubscriptions[bot.id] && (
                      <>
                        {/* Categories */}
                        {botSubscriptions[bot.id].categories && botSubscriptions[bot.id].categories.length > 0 && (
                          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 1 }}>
                            <CategoryIcon fontSize="small" color="action" sx={{ mt: 0.5 }} />
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, flex: 1 }}>
                              {botSubscriptions[bot.id].categories
                                .sort((a, b) => (a.priority || 0) - (b.priority || 0))
                                .map((category, index) => (
                                  <Chip
                                    key={category.id || index}
                                    label={`${category.category_name || category.name}${category.priority ? `(${category.priority})` : ''}`}
                                    size="small"
                                    variant="outlined"
                                    color="primary"
                                    sx={{ fontSize: '0.75rem', height: '20px' }}
                                  />
                                ))}
                            </Box>
                          </Box>
                        )}
                        
                        {/* Channels */}
                        {botSubscriptions[bot.id].channels && botSubscriptions[bot.id].channels.length > 0 && (
                          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                            <ChannelIcon fontSize="small" color="action" sx={{ mt: 0.5 }} />
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, flex: 1 }}>
                              {botSubscriptions[bot.id].channels.map((channel, index) => (
                                <Chip
                                  key={channel.id || index}
                                  label={channel.username || channel.channel_name || channel.title || `ID:${channel.telegram_id}`}
                                  size="small"
                                  variant="outlined"
                                  color="secondary"
                                  sx={{ fontSize: '0.75rem', height: '20px' }}
                                />
                              ))}
                            </Box>
                          </Box>
                        )}
                      </>
                    )}
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
                <Box sx={{ p: 2, pt: 0, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: 1, borderColor: 'divider' }}>
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
                        onClick={() => handleGeneratePreview(bot)}
                      >
                        <PreviewIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                  
                  {/* Status and Control Block */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip 
                      label={getStatusText(bot.status)}
                      color={getStatusColor(bot.status)}
                      size="small"
                    />
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
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Создать нового бота</DialogTitle>
        <DialogContent>
          <BotConfigurationTabs 
            bot={formData} 
            onBotUpdate={(updatedBot) => setFormData(updatedBot)}
            onClose={() => setCreateDialogOpen(false)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Отмена</Button>
          <Button 
            onClick={handleFillDefaults}
            variant="outlined"
            sx={{ mr: 'auto' }}
          >
            Заполнить дефолтными значениями
          </Button>
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
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PreviewIcon />
            Превью дайджеста {selectedBot?.name}
          </Box>
        </DialogTitle>
        <DialogContent>
          {previewLoading ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
              <CircularProgress sx={{ mb: 2 }} />
              <Typography variant="body2" color="text.secondary">
                Генерируем превью дайджеста...
              </Typography>
            </Box>
          ) : previewData ? (
            previewData.success ? (
              <Box sx={{ mt: 2 }}>
                {/* Bot Info */}
                <Card sx={{ mb: 3, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      🤖 {previewData.bot_info.name}
                    </Typography>
                    <Typography variant="body2">
                      {previewData.bot_info.description || 'Описание не указано'}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                      <Chip label={`Язык: ${previewData.bot_info.language.toUpperCase()}`} size="small" />
                      <Chip label={`Макс. постов: ${previewData.bot_info.max_posts}`} size="small" />
                      <Chip label={`Макс. длина: ${previewData.bot_info.max_summary_length}`} size="small" />
                    </Box>
                  </CardContent>
                </Card>

                {/* Digest Stats */}
                <Card sx={{ mb: 3, bgcolor: 'success.light', color: 'success.contrastText' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      📊 Статистика дайджеста
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" component="div">Проанализировано:</Typography>
                        <Typography variant="h6" component="div">{previewData.preview_data.total_posts_analyzed}</Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" component="div">В превью:</Typography>
                        <Typography variant="h6" component="div">{previewData.preview_data.posts_in_preview}</Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" component="div">AI обработано:</Typography>
                        <Typography variant="h6" component="div" color={previewData.preview_data.ai_processed_posts > 0 ? 'success.main' : 'warning.main'}>
                          {previewData.preview_data.ai_processed_posts}/{previewData.preview_data.posts_in_preview}
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" component="div">Каналов:</Typography>
                        <Typography variant="h6" component="div">{previewData.preview_data.channels_count}</Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" component="div">Важность:</Typography>
                        <Typography variant="h6" component="div">{previewData.digest_stats.avg_importance.toFixed(1)}</Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" component="div">Срочность:</Typography>
                        <Typography variant="h6" component="div">{previewData.digest_stats.avg_urgency.toFixed(1)}</Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" component="div">Значимость:</Typography>
                        <Typography variant="h6" component="div">{previewData.digest_stats.avg_significance.toFixed(1)}</Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" component="div">Просмотры:</Typography>
                        <Typography variant="h6" component="div">{previewData.digest_stats.total_views}</Typography>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>

                {/* Channels Info */}
                {previewData.channels_info && previewData.channels_info.length > 0 && (
                  <Card sx={{ mb: 3, bgcolor: 'info.light', color: 'info.contrastText' }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        📺 Каналы бота
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        {previewData.channels_info.map((channel) => (
                          <Chip 
                            key={channel.id}
                            label={`${channel.name} (@${channel.username || channel.telegram_id})`}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    </CardContent>
                  </Card>
                )}

                {/* Posts Preview */}
                <Typography variant="h6" gutterBottom>
                  📝 Посты в дайджесте
                </Typography>
                {previewData.preview_data.posts.map((post, index) => (
                  <Card key={post.post_id} sx={{ mb: 2 }}>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="h6" component="div">
                          {post.title}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                          <Chip 
                            label={post.category} 
                            color={post.ai_processed ? "primary" : "default"}
                            size="small"
                          />
                          {post.ai_processed ? (
                            <Chip label="AI ✓" color="success" size="small" />
                          ) : (
                            <Chip label="Ожидает" color="warning" size="small" />
                          )}
                        </Box>
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        📺 Канал: {post.channel_name}
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {post.content_preview}
                      </Typography>
                      
                      <Box sx={{ bgcolor: post.ai_processed ? 'success.light' : 'grey.50', p: 2, borderRadius: 1, mb: 2 }}>
                        <Typography variant="subtitle2" color={post.ai_processed ? "success.dark" : "primary"} gutterBottom>
                          {post.ai_processed ? "🧠 AI Резюме:" : "📄 Предварительное резюме:"}
                        </Typography>
                        <Typography variant="body2">
                          {post.summary}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <Chip label={`Важность: ${post.metrics.importance}`} size="small" color="info" />
                        <Chip label={`Срочность: ${post.metrics.urgency}`} size="small" color="warning" />
                        <Chip label={`Значимость: ${post.metrics.significance}`} size="small" color="success" />
                        <Chip label={`Просмотры: ${post.views}`} size="small" />
                      </Box>
                    </CardContent>
                  </Card>
                ))}

                {/* AI Processing Info */}
                <Card sx={{ mt: 3, bgcolor: previewData.ai_processing.status === 'real' ? 'success.light' : 'warning.light', 
                           color: previewData.ai_processing.status === 'real' ? 'success.contrastText' : 'warning.contrastText' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      🧠 AI Обработка
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 2 }}>
                      {previewData.ai_processing.note}
                    </Typography>
                    
                    {previewData.ai_processing.status === 'real' && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          📈 Статус обработки:
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                          <Chip 
                            label={`Обработано: ${previewData.ai_processing.processed_posts}`} 
                            color="success" 
                            size="small" 
                          />
                          {previewData.ai_processing.pending_posts > 0 && (
                            <Chip 
                              label={`Ожидает: ${previewData.ai_processing.pending_posts}`} 
                              color="warning" 
                              size="small" 
                            />
                          )}
                        </Box>
                      </Box>
                    )}
                    
                    {previewData.ai_processing.categorization_prompt && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="subtitle2" component="div">Промпт категоризации:</Typography>
                        <Typography variant="body2" component="div" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                          {previewData.ai_processing.categorization_prompt}
                        </Typography>
                      </Box>
                    )}
                    {previewData.ai_processing.summarization_prompt && (
                      <Box>
                        <Typography variant="subtitle2" component="div">Промпт суммаризации:</Typography>
                        <Typography variant="body2" component="div" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                          {previewData.ai_processing.summarization_prompt}
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Box>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="h6" color="error" gutterBottom>
                  ⚠️ Ошибка генерации превью
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {previewData.error}
                </Typography>
                {previewData.fallback_data && (
                  <Typography variant="body2">
                    {previewData.fallback_data.message}
                  </Typography>
                )}
              </Box>
            )
          ) : (
            <Typography variant="body2" color="text.secondary">
              Нажмите кнопку для генерации превью дайджеста
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialogOpen(false)}>Закрыть</Button>
          {previewData && !previewData.success && (
            <Button 
              variant="contained" 
              onClick={() => handleGeneratePreview(selectedBot)}
              disabled={previewLoading}
            >
              Попробовать снова
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => !deleting && setDeleteDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ color: 'error.main' }}>
          ⚠️ Подтверждение удаления
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Вы уверены, что хотите удалить бота <strong>"{selectedBot?.name}"</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Это действие нельзя отменить. Будут удалены:
          </Typography>
          <Box component="ul" sx={{ mt: 1, pl: 2 }}>
            <Typography component="li" variant="body2" color="text.secondary">
              Все настройки бота
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              Связи с каналами и категориями
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              История дайджестов
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setDeleteDialogOpen(false)}
            disabled={deleting}
          >
            Отмена
          </Button>
          <Button 
            onClick={handleDeleteBot}
            color="error"
            variant="contained"
            disabled={deleting}
            startIcon={deleting ? <CircularProgress size={16} /> : <DeleteIcon />}
          >
            {deleting ? 'Удаление...' : 'Удалить бота'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default PublicBotsPage; 