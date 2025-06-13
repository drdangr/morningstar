import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Button,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Chip,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Snackbar,
  Tabs,
  Tab
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Restore as RestoreIcon,
  Psychology as AIIcon,
  Settings as SystemIcon,
  Article as DigestIcon,
  Info as InfoIcon,
  Public as GlobalIcon,
  SmartToy as BotTemplateIcon
} from '@mui/icons-material';

const API_BASE_URL = 'http://localhost:8000';

// Конфигурация табов
const TABS_CONFIG = {
  global: {
    id: 'global',
    label: 'Глобальные настройки',
    icon: <GlobalIcon />,
    description: 'Настройки для всей системы MorningStarBot3'
  },
  template: {
    id: 'template',
    label: 'Шаблон Public Bot',
    icon: <BotTemplateIcon />,
    description: 'Значения по умолчанию для новых публичных ботов'
  }
};

// Конфигурация категорий настроек
const SETTING_CATEGORIES = {
  ai: {
    title: 'AI и LLM Настройки',
    icon: <AIIcon />,
    color: 'primary',
    description: 'Управление искусственным интеллектом и языковыми моделями'
  },
  system: {
    title: 'Системные Настройки',
    icon: <SystemIcon />,
    color: 'secondary',
    description: 'Общие настройки системы и производительности'
  },
  digest: {
    title: 'Настройки Дайджестов',
    icon: <DigestIcon />,
    color: 'success',
    description: 'Параметры генерации и доставки дайджестов'
  }
};

// Настройки шаблона бота (по умолчанию для новых ботов)
const BOT_TEMPLATE_SETTINGS = {
  ai: [
    {
      key: 'DEFAULT_AI_MODEL',
      description: 'Модель AI по умолчанию для новых ботов',
      value_type: 'string',
      is_editable: true,
      category: 'ai'
    },
    {
      key: 'DEFAULT_MAX_TOKENS',
      description: 'Максимальное количество токенов для новых ботов',
      value_type: 'integer',
      is_editable: true,
      category: 'ai'
    },
    {
      key: 'DEFAULT_TEMPERATURE',
      description: 'Температура AI для новых ботов (0.0-2.0)',
      value_type: 'float',
      is_editable: true,
      category: 'ai'
    },
    {
      key: 'DEFAULT_CATEGORIZATION_PROMPT',
      description: 'Промпт для категоризации постов по умолчанию',
      value_type: 'string',
      is_editable: true,
      category: 'ai'
    },
    {
      key: 'DEFAULT_SUMMARIZATION_PROMPT',
      description: 'Промпт для суммаризации постов по умолчанию',
      value_type: 'string',
      is_editable: true,
      category: 'ai'
    }
  ],
  digest: [
    {
      key: 'DEFAULT_MAX_POSTS_PER_DIGEST',
      description: 'Максимальное количество постов в дайджесте по умолчанию',
      value_type: 'integer',
      is_editable: true,
      category: 'digest'
    },
    {
      key: 'DEFAULT_MAX_SUMMARY_LENGTH',
      description: 'Максимальная длина резюме по умолчанию',
      value_type: 'integer',
      is_editable: true,
      category: 'digest'
    },
    {
      key: 'DEFAULT_DIGEST_LANGUAGE',
      description: 'Язык дайджестов по умолчанию',
      value_type: 'string',
      is_editable: true,  
      category: 'digest'
    }
  ]
};

// Специальные компоненты для разных типов настроек
const SettingField = ({ setting, value, onChange, disabled, isTemplate = false }) => {
  const handleChange = (newValue) => {
    onChange(setting.key, newValue, setting.value_type);
  };

  const getLabel = (key) => {
    if (isTemplate && key.startsWith('DEFAULT_')) {
      return key.replace('DEFAULT_', '').replace(/_/g, ' ');
    }
    return key.replace(/_/g, ' ');
  };

  switch (setting.value_type) {
    case 'boolean':
      return (
        <FormControlLabel
          control={
            <Switch
              checked={value === 'true' || value === true}
              onChange={(e) => handleChange(e.target.checked.toString())}
              disabled={disabled || !setting.is_editable}
              color="primary"
            />
          }
          label={getLabel(setting.key).toLowerCase()}
        />
      );

    case 'integer':
      return (
        <TextField
          fullWidth
          type="number"
          label={getLabel(setting.key)}
          value={value || ''}
          onChange={(e) => handleChange(e.target.value)}
          disabled={disabled || !setting.is_editable}
          inputProps={{ min: 0 }}
          helperText={setting.description}
        />
      );

    case 'float':
      return (
        <TextField
          fullWidth
          type="number"
          label={getLabel(setting.key)}
          value={value || ''}
          onChange={(e) => handleChange(e.target.value)}
          disabled={disabled || !setting.is_editable}
          inputProps={{ min: 0, step: 0.1 }}
          helperText={setting.description}
        />
      );

    default: // string
      if (setting.key === 'AI_MODEL' || setting.key === 'DEFAULT_AI_MODEL') {
        return (
          <FormControl fullWidth disabled={disabled || !setting.is_editable}>
            <InputLabel>{getLabel(setting.key)}</InputLabel>
            <Select
              value={value || ''}
              label={getLabel(setting.key)}
              onChange={(e) => handleChange(e.target.value)}
            >
              <MenuItem value="gpt-4">GPT-4 (Рекомендуется)</MenuItem>
              <MenuItem value="gpt-4-turbo">GPT-4 Turbo</MenuItem>
              <MenuItem value="gpt-3.5-turbo">GPT-3.5 Turbo</MenuItem>
              <MenuItem value="gpt-4o-mini">GPT-4o Mini</MenuItem>
            </Select>
          </FormControl>
        );
      }

      if (setting.key === 'DEFAULT_DIGEST_LANGUAGE') {
        return (
          <FormControl fullWidth disabled={disabled || !setting.is_editable}>
            <InputLabel>Язык по умолчанию</InputLabel>
            <Select
              value={value || ''}
              label="Язык по умолчанию"
              onChange={(e) => handleChange(e.target.value)}
            >
              <MenuItem value="ru">Русский</MenuItem>
              <MenuItem value="en">English</MenuItem>
              <MenuItem value="uk">Українська</MenuItem>
            </Select>
          </FormControl>
        );
      }

      return (
        <TextField
          fullWidth
          label={getLabel(setting.key)}
          value={value || ''}
          onChange={(e) => handleChange(e.target.value)}
          disabled={disabled || !setting.is_editable}
          helperText={setting.description}
          multiline={setting.description && setting.description.length > 50}
          rows={setting.description && setting.description.length > 50 ? 3 : 1}
        />
      );
  }
};

function LLMSettingsPage() {
  const [activeTab, setActiveTab] = useState('global');
  const [settings, setSettings] = useState([]);
  const [changedSettings, setChangedSettings] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [expandedCategory, setExpandedCategory] = useState('ai');

  // Загрузка настроек
  const loadSettings = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/settings`);
      const data = await response.json();
      setSettings(data);
    } catch (err) {
      setError('Ошибка загрузки настроек: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Обработка изменения настройки
  const handleSettingChange = (key, value, valueType) => {
    setChangedSettings(prev => ({
      ...prev,
      [key]: { value, value_type: valueType }
    }));
  };

  // Получение значения настройки для шаблона
  const getTemplateValue = (key) => {
    // Здесь будет логика получения значений шаблона из API
    // Пока возвращаем значения по умолчанию
    const templateDefaults = {
      'DEFAULT_AI_MODEL': 'gpt-4o-mini',
      'DEFAULT_MAX_TOKENS': '4000',
      'DEFAULT_TEMPERATURE': '0.3',
      'DEFAULT_MAX_POSTS_PER_DIGEST': '10',
      'DEFAULT_MAX_SUMMARY_LENGTH': '150',
      'DEFAULT_DIGEST_LANGUAGE': 'ru',
      'DEFAULT_CATEGORIZATION_PROMPT': 'Проанализируй пост и определи наиболее подходящую категорию из предложенного списка. Учитывай контекст и семантическое значение.',
      'DEFAULT_SUMMARIZATION_PROMPT': 'Создай краткое и информативное резюме поста на русском языке. Сохрани ключевые факты и важные детали.'
    };
    return templateDefaults[key] || '';
  };

  // Сохранение всех изменений
  const handleSaveAll = async () => {
    if (Object.keys(changedSettings).length === 0) {
      setSuccessMessage('Нет изменений для сохранения');
      return;
    }

    setSaving(true);
    setError('');

    try {
      // TODO: Здесь будет API для сохранения настроек шаблона
      setSuccessMessage(`Сохранено ${Object.keys(changedSettings).length} настроек`);
      setChangedSettings({});
    } catch (err) {
      setError('Ошибка сохранения: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  // Сброс изменений
  const handleResetChanges = () => {
    setChangedSettings({});
    setSuccessMessage('Изменения сброшены');
  };

  // Загрузка при монтировании
  useEffect(() => {
    loadSettings();
  }, []);

  // Группировка настроек по категориям
  const groupedSettings = settings.reduce((acc, setting) => {
    const category = setting.category || 'system';
    if (!acc[category]) acc[category] = [];
    acc[category].push(setting);
    return acc;
  }, {});

  // Получение текущего значения настройки (с учетом изменений)
  const getCurrentValue = (setting) => {
    return changedSettings[setting.key]?.value ?? setting.value;
  };

  // Подсчет изменений по категориям
  const getChangesCount = (category) => {
    return Object.keys(changedSettings).filter(key => {
      const setting = settings.find(s => s.key === key);
      return setting && setting.category === category;
    }).length;
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          AI и LLM Настройки
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Перезагрузить настройки">
            <IconButton onClick={loadSettings} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Сбросить изменения">
            <IconButton 
              onClick={handleResetChanges} 
              disabled={Object.keys(changedSettings).length === 0}
            >
              <RestoreIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSaveAll}
            disabled={saving || Object.keys(changedSettings).length === 0}
            sx={{ ml: 1 }}
          >
            {saving ? 'Сохранение...' : `Сохранить (${Object.keys(changedSettings).length})`}
          </Button>
        </Box>
      </Box>

      {/* Табы для разделения глобальных настроек и шаблона */}
      <Paper sx={{ mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={(e, newValue) => setActiveTab(newValue)}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          {Object.values(TABS_CONFIG).map(tab => (
            <Tab
              key={tab.id}
              value={tab.id}
              icon={tab.icon}
              label={tab.label}
              iconPosition="start"
            />
          ))}
        </Tabs>
        
        {/* Описание активного таба */}
        <Box sx={{ p: 2, bgcolor: 'grey.50' }}>
          <Typography variant="body2" color="textSecondary">
            {TABS_CONFIG[activeTab]?.description}
          </Typography>
        </Box>
      </Paper>

      {/* Ошибки */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Информация об изменениях */}
      {Object.keys(changedSettings).length > 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <InfoIcon />
            <Typography>
              Изменено настроек: {Object.keys(changedSettings).length}. 
              Не забудьте сохранить изменения.
            </Typography>
          </Box>
        </Alert>
      )}

      {/* Контент таба */}
      {activeTab === 'global' && (
        <Box>
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Глобальные настройки</strong> действуют для всей системы и наследуются всеми ботами.
              Эти настройки можно переопределить в шаблоне бота или в настройках конкретного бота.
            </Typography>
          </Alert>
          
          {/* Глобальные настройки по категориям */}
          {Object.entries(SETTING_CATEGORIES).map(([categoryKey, categoryConfig]) => {
            const categorySettings = groupedSettings[categoryKey] || [];
            const changesCount = getChangesCount(categoryKey);
            
            if (categorySettings.length === 0) return null;

            return (
              <Accordion
                key={categoryKey}
                expanded={expandedCategory === categoryKey}
                onChange={() => setExpandedCategory(expandedCategory === categoryKey ? '' : categoryKey)}
                sx={{ mb: 2 }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                    {categoryConfig.icon}
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6">
                        {categoryConfig.title}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {categoryConfig.description}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip 
                        label={`${categorySettings.length} настроек`} 
                        size="small" 
                        color={categoryConfig.color}
                        variant="outlined"
                      />
                      {changesCount > 0 && (
                        <Chip 
                          label={`${changesCount} изменений`} 
                          size="small" 
                          color="warning"
                        />
                      )}
                    </Box>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={3}>
                    {categorySettings.map((setting) => (
                      <Grid item xs={12} md={6} key={setting.id}>
                        <Card variant="outlined">
                          <CardContent>
                            <Box sx={{ mb: 2 }}>
                              <Typography variant="h6" gutterBottom>
                                {setting.key.replace(/_/g, ' ')}
                              </Typography>
                              {setting.description && (
                                <Typography variant="body2" color="textSecondary" gutterBottom>
                                  {setting.description}
                                </Typography>
                              )}
                              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                                <Chip 
                                  label={setting.value_type} 
                                  size="small" 
                                  variant="outlined"
                                />
                                {!setting.is_editable && (
                                  <Chip 
                                    label="Только чтение" 
                                    size="small" 
                                    color="default"
                                  />
                                )}
                                {changedSettings[setting.key] && (
                                  <Chip 
                                    label="Изменено" 
                                    size="small" 
                                    color="warning"
                                  />
                                )}
                              </Box>
                            </Box>
                            
                            <SettingField
                              setting={setting}
                              value={getCurrentValue(setting)}
                              onChange={handleSettingChange}
                              disabled={loading || saving}
                            />
                            
                            {setting.value !== getCurrentValue(setting) && (
                              <Box sx={{ mt: 1, p: 1, bgcolor: 'warning.light', borderRadius: 1 }}>
                                <Typography variant="caption">
                                  Было: {setting.value} → Будет: {getCurrentValue(setting)}
                                </Typography>
                              </Box>
                            )}
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </AccordionDetails>
              </Accordion>
            );
          })}
        </Box>
      )}

      {activeTab === 'template' && (
        <Box>
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Шаблон Public Bot</strong> - это настройки по умолчанию для новых ботов.
              При создании нового бота эти значения будут использованы как начальные.
              Каждый бот может переопределить эти настройки индивидуально.
            </Typography>
          </Alert>
          
          {/* Настройки шаблона бота */}
          {Object.entries(SETTING_CATEGORIES).map(([categoryKey, categoryConfig]) => {
            const categorySettings = BOT_TEMPLATE_SETTINGS[categoryKey] || [];
            
            if (categorySettings.length === 0) return null;

            return (
              <Accordion
                key={`template-${categoryKey}`}
                expanded={expandedCategory === `template-${categoryKey}`}
                onChange={() => setExpandedCategory(expandedCategory === `template-${categoryKey}` ? '' : `template-${categoryKey}`)}
                sx={{ mb: 2 }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                    {categoryConfig.icon}
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6">
                        {categoryConfig.title} (Шаблон)
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Значения по умолчанию для новых ботов
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip 
                        label={`${categorySettings.length} настроек`} 
                        size="small" 
                        color={categoryConfig.color}
                        variant="outlined"
                      />
                    </Box>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={3}>
                    {categorySettings.map((setting) => (
                      <Grid item xs={12} md={6} key={setting.key}>
                        <Card variant="outlined">
                          <CardContent>
                            <Box sx={{ mb: 2 }}>
                              <Typography variant="h6" gutterBottom>
                                {setting.key.replace('DEFAULT_', '').replace(/_/g, ' ')}
                              </Typography>
                              {setting.description && (
                                <Typography variant="body2" color="textSecondary" gutterBottom>
                                  {setting.description}
                                </Typography>
                              )}
                              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                                <Chip 
                                  label={setting.value_type} 
                                  size="small" 
                                  variant="outlined"
                                />
                                <Chip 
                                  label="Шаблон" 
                                  size="small" 
                                  color="info"
                                />
                              </Box>
                            </Box>
                            
                            <SettingField
                              setting={setting}
                              value={getTemplateValue(setting.key)}
                              onChange={handleSettingChange}
                              disabled={loading || saving}
                              isTemplate={true}
                            />
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </AccordionDetails>
              </Accordion>
            );
          })}
        </Box>
      )}

      {/* Snackbar для успешных сообщений */}
      <Snackbar
        open={!!successMessage}
        autoHideDuration={3000}
        onClose={() => setSuccessMessage('')}
        message={successMessage}
      />
    </Box>
  );
}

export default LLMSettingsPage; 