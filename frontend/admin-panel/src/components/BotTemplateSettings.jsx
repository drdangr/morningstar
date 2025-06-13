import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Paper,
  Divider,
  Chip
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Restore as RestoreIcon,
  Psychology as AIIcon,
  Article as DigestIcon,
  Schedule as DeliveryIcon,
  Settings as SystemIcon,
  SmartToy as BotTemplateIcon
} from '@mui/icons-material';

const COMMON_TIMEZONES = [
  'Europe/Moscow',
  'Europe/Kiev',
  'Europe/Minsk',
  'UTC',
  'Europe/London',
  'Europe/Berlin',
  'America/New_York',
  'America/Los_Angeles',
  'Asia/Tokyo'
];

const AI_MODELS = [
  'gpt-4o',
  'gpt-4o-mini',
  'gpt-4-turbo',
  'gpt-3.5-turbo'
];

const LANGUAGES = [
  { value: 'ru', label: 'Русский' },
  { value: 'en', label: 'English' },
  { value: 'uk', label: 'Українська' }
];

const BotTemplateSettings = () => {
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  // Загрузка настроек при монтировании
  useEffect(() => {
    loadTemplateSettings();
  }, []);

  const loadTemplateSettings = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/bot-templates');
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
        setHasChanges(false);
      } else {
        throw new Error('Ошибка загрузки настроек шаблона');
      }
    } catch (err) {
      setError('Ошибка загрузки настроек: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
    setHasChanges(true);
  };

  const saveTemplateSettings = async () => {
    setSaving(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/bot-templates', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (response.ok) {
        setSuccessMessage('Настройки шаблона сохранены успешно');
        setHasChanges(false);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка сохранения настроек');
      }
    } catch (err) {
      setError('Ошибка сохранения: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const resetToDefaults = () => {
    const defaultSettings = {
      default_ai_model: 'gpt-4o-mini',
      default_max_tokens: 4000,
      default_temperature: 0.7,
      default_categorization_prompt: 'Анализируй посты и определи их категорию...',
      default_summarization_prompt: 'Создай краткое резюме поста...',
      default_max_posts_per_digest: 15,
      default_max_summary_length: 200,
      default_digest_language: 'ru',
      default_welcome_message: 'Добро пожаловать в USA News Bot!',
      default_delivery_schedule: {
        monday: ['08:00', '19:00'],
        tuesday: ['08:00', '19:00'],
        wednesday: ['08:00', '19:00'],
        thursday: ['08:00', '19:00'],
        friday: ['08:00', '19:00'],
        saturday: ['10:00'],
        sunday: ['10:00']
      },
      default_timezone: 'Europe/Moscow'
    };
    setSettings(defaultSettings);
    setHasChanges(true);
  };

  if (loading) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography>Загрузка настроек шаблона...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Заголовок и действия */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BotTemplateIcon />
            Шаблон настроек для новых ботов
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Настройте значения по умолчанию, которые будут применяться к новым публичным ботам
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Перезагрузить настройки">
            <IconButton onClick={loadTemplateSettings} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Сбросить к значениям по умолчанию">
            <IconButton onClick={resetToDefaults}>
              <RestoreIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={saveTemplateSettings}
            disabled={saving || !hasChanges}
          >
            {saving ? 'Сохранение...' : 'Сохранить'}
          </Button>
        </Box>
      </Box>

      {/* Ошибки и успешные сообщения */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {successMessage && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccessMessage('')}>
          {successMessage}
        </Alert>
      )}

      {/* Индикатор изменений */}
      {hasChanges && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          У вас есть несохраненные изменения. Не забудьте сохранить настройки.
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Верхний ряд: AI настройки */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AIIcon />
                AI и LLM Настройки
                <Chip label="5 настроек" size="small" color="primary" variant="outlined" />
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>AI Модель по умолчанию</InputLabel>
                    <Select
                      value={settings.default_ai_model || ''}
                      onChange={(e) => handleSettingChange('default_ai_model', e.target.value)}
                      label="AI Модель по умолчанию"
                    >
                      {AI_MODELS.map((model) => (
                        <MenuItem key={model} value={model}>
                          {model}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} md={3}>
                  <TextField
                    fullWidth
                    size="small"
                    type="number"
                    label="Макс. токенов"
                    value={settings.default_max_tokens || ''}
                    onChange={(e) => handleSettingChange('default_max_tokens', parseInt(e.target.value))}
                    inputProps={{ min: 1000, max: 8000 }}
                  />
                </Grid>
                
                <Grid item xs={12} md={3}>
                  <TextField
                    fullWidth
                    size="small"
                    type="number"
                    label="Температура"
                    value={settings.default_temperature || ''}
                    onChange={(e) => handleSettingChange('default_temperature', parseFloat(e.target.value))}
                    inputProps={{ min: 0, max: 2, step: 0.1 }}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        multiline
                        rows={3}
                        label="Промпт для категоризации"
                        value={settings.default_categorization_prompt || ''}
                        onChange={(e) => handleSettingChange('default_categorization_prompt', e.target.value)}
                        helperText="Инструкции для AI по категоризации постов"
                      />
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        multiline
                        rows={3}
                        label="Промпт для суммаризации"
                        value={settings.default_summarization_prompt || ''}
                        onChange={(e) => handleSettingChange('default_summarization_prompt', e.target.value)}
                        helperText="Инструкции для AI по созданию резюме"
                      />
                    </Grid>
                  </Grid>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Нижний ряд: Настройки Дайджестов и Доставки */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <DigestIcon />
                Настройки Дайджестов
                <Chip label="4 настройки" size="small" color="success" variant="outlined" />
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    size="small"
                    type="number"
                    label="Макс. постов в дайджесте"
                    value={settings.default_max_posts_per_digest || ''}
                    onChange={(e) => handleSettingChange('default_max_posts_per_digest', parseInt(e.target.value))}
                    inputProps={{ min: 5, max: 50 }}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    size="small"
                    type="number"
                    label="Макс. длина резюме"
                    value={settings.default_max_summary_length || ''}
                    onChange={(e) => handleSettingChange('default_max_summary_length', parseInt(e.target.value))}
                    inputProps={{ min: 50, max: 500 }}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Язык дайджеста</InputLabel>
                    <Select
                      value={settings.default_digest_language || ''}
                      onChange={(e) => handleSettingChange('default_digest_language', e.target.value)}
                      label="Язык дайджеста"
                    >
                      {LANGUAGES.map((lang) => (
                        <MenuItem key={lang.value} value={lang.value}>
                          {lang.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Приветственное сообщение"
                    value={settings.default_welcome_message || ''}
                    onChange={(e) => handleSettingChange('default_welcome_message', e.target.value)}
                    helperText="Сообщение для новых подписчиков"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <DeliveryIcon />
                Настройки Доставки
                <Chip label="2 настройки" size="small" color="info" variant="outlined" />
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Часовой пояс по умолчанию</InputLabel>
                    <Select
                      value={settings.default_timezone || ''}
                      onChange={(e) => handleSettingChange('default_timezone', e.target.value)}
                      label="Часовой пояс по умолчанию"
                    >
                      {COMMON_TIMEZONES.map((tz) => (
                        <MenuItem key={tz} value={tz}>
                          {tz}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={8}
                    label="Расписание доставки (JSON)"
                    value={typeof settings.default_delivery_schedule === 'object' 
                      ? JSON.stringify(settings.default_delivery_schedule, null, 2) 
                      : settings.default_delivery_schedule || '{}'}
                    onChange={(e) => {
                      try {
                        const parsed = JSON.parse(e.target.value);
                        handleSettingChange('default_delivery_schedule', parsed);
                      } catch {
                        handleSettingChange('default_delivery_schedule', e.target.value);
                      }
                    }}
                    helperText="Формат: {'monday': ['08:00', '19:00'], 'tuesday': ['08:00', '19:00'], ...}"
                    sx={{
                      '& .MuiInputBase-root': {
                        fontFamily: 'monospace',
                        fontSize: '0.875rem'
                      }
                    }}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default BotTemplateSettings; 