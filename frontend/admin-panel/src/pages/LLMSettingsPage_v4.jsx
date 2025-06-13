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
  Divider,
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
  SmartToy as BotTemplateIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';

import BotTemplateSettings from '../components/BotTemplateSettings';

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
  digest: {
    title: 'Настройки Дайджестов',
    icon: <DigestIcon />,
    color: 'success',
    description: 'Параметры генерации и доставки дайджестов'
  },
  delivery: {
    title: 'Настройки Доставки',
    icon: <ScheduleIcon />,
    color: 'info',
    description: 'Расписание и параметры доставки дайджестов'
  },
  system: {
    title: 'Системные Настройки',
    icon: <SystemIcon />,
    color: 'secondary',
    description: 'Общие настройки системы и производительности'
  }
};

// Специальные компоненты для разных типов настроек
const SettingField = ({ setting, value, onChange, disabled, isTemplate = false }) => {
  const handleChange = (newValue) => {
    onChange(setting.key, newValue, setting.value_type);
  };

  const getLabel = (key) => {
    if (isTemplate && key.startsWith('default_')) {
      return key.replace('default_', '').replace(/_/g, ' ');
    }
    return key.replace(/_/g, ' ');
  };

  // Специальная обработка для delivery_schedule
  if (setting.key === 'default_delivery_schedule' && isTemplate) {
    return (
      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Расписание доставки по умолчанию
        </Typography>
        <TextField
          fullWidth
          multiline
          rows={8}
          label="JSON расписание"
          value={typeof value === 'object' ? JSON.stringify(value, null, 2) : value || '{}'}
          onChange={(e) => {
            try {
              const parsed = JSON.parse(e.target.value);
              handleChange(parsed);
            } catch {
              handleChange(e.target.value);
            }
          }}
          disabled={disabled || !setting.is_editable}
          helperText="Формат: {'monday': ['08:00', '19:00'], 'tuesday': ['08:00', '19:00'], ...}"
        />
      </Box>
    );
  }

  // Специальная обработка для промптов
  if (setting.key.includes('prompt')) {
    return (
      <TextField
        fullWidth
        multiline
        rows={6}
        label={getLabel(setting.key)}
        value={value || ''}
        onChange={(e) => handleChange(e.target.value)}
        disabled={disabled || !setting.is_editable}
        helperText={setting.description}
      />
    );
  }

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

    default:
      return (
        <TextField
          fullWidth
          label={getLabel(setting.key)}
          value={value || ''}
          onChange={(e) => handleChange(e.target.value)}
          disabled={disabled || !setting.is_editable}
          helperText={setting.description}
        />
      );
  }
};

function LLMSettingsPage() {
  const [activeTab, setActiveTab] = useState('global');
  const [settings, setSettings] = useState([]);
  const [templateSettings, setTemplateSettings] = useState(null);
  const [changedSettings, setChangedSettings] = useState({});
  const [changedTemplateSettings, setChangedTemplateSettings] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [expandedCategory, setExpandedCategory] = useState('ai');

  // Загрузка глобальных настроек
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

  // Загрузка шаблонных настроек
  const loadTemplateSettings = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/bot-templates`);
      const data = await response.json();
      setTemplateSettings(data);
    } catch (err) {
      setError('Ошибка загрузки шаблонных настроек: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Обработка изменения глобальной настройки
  const handleSettingChange = (key, value, valueType) => {
    setChangedSettings(prev => ({
      ...prev,
      [key]: { value, value_type: valueType }
    }));
  };

  // Обработка изменения шаблонной настройки
  const handleTemplateSettingChange = (key, value, valueType) => {
    setChangedTemplateSettings(prev => ({
      ...prev,
      [key]: { value, value_type: valueType }
    }));
  };

  // Получение настроек для текущего таба
  const getCurrentSettings = () => {
    if (activeTab === 'template') {
      // Преобразуем шаблонные настройки в формат для отображения
      if (!templateSettings) return [];
      
      return [
        // AI Settings
        {
          key: 'default_ai_model',
          description: 'Модель AI по умолчанию для новых ботов',
          value: templateSettings.default_ai_model,
          value_type: 'string',
          is_editable: true,
          category: 'ai'
        },
        {
          key: 'default_max_tokens',
          description: 'Максимальное количество токенов для новых ботов',
          value: templateSettings.default_max_tokens,
          value_type: 'integer',
          is_editable: true,
          category: 'ai'
        },
        {
          key: 'default_temperature',
          description: 'Температура AI для новых ботов (0.0-2.0)',
          value: templateSettings.default_temperature,
          value_type: 'float',
          is_editable: true,
          category: 'ai'
        },
        {
          key: 'default_categorization_prompt',
          description: 'Промпт для категоризации постов по умолчанию',
          value: templateSettings.default_categorization_prompt,
          value_type: 'string',
          is_editable: true,
          category: 'ai'
        },
        {
          key: 'default_summarization_prompt',
          description: 'Промпт для суммаризации постов по умолчанию',
          value: templateSettings.default_summarization_prompt,
          value_type: 'string',
          is_editable: true,
          category: 'ai'
        },
        // Digest Settings
        {
          key: 'default_max_posts_per_digest',
          description: 'Максимальное количество постов в дайджесте по умолчанию',
          value: templateSettings.default_max_posts_per_digest,
          value_type: 'integer',
          is_editable: true,
          category: 'digest'
        },
        {
          key: 'default_max_summary_length',
          description: 'Максимальная длина резюме по умолчанию',
          value: templateSettings.default_max_summary_length,
          value_type: 'integer',
          is_editable: true,
          category: 'digest'
        },
        {
          key: 'default_digest_language',
          description: 'Язык дайджестов по умолчанию',
          value: templateSettings.default_digest_language,
          value_type: 'string',
          is_editable: true,
          category: 'digest'
        },
        {
          key: 'default_welcome_message',
          description: 'Приветственное сообщение по умолчанию',
          value: templateSettings.default_welcome_message,
          value_type: 'string',
          is_editable: true,
          category: 'digest'
        },
        // Delivery Settings
        {
          key: 'default_delivery_schedule',
          description: 'Расписание доставки по умолчанию',
          value: templateSettings.default_delivery_schedule,
          value_type: 'json',
          is_editable: true,
          category: 'delivery'
        },
        {
          key: 'default_timezone',
          description: 'Часовой пояс по умолчанию',
          value: templateSettings.default_timezone,
          value_type: 'string',
          is_editable: true,
          category: 'delivery'
        }
      ];
    }
    return settings; // Глобальные настройки
  };

  // Сохранение всех изменений
  const handleSaveAll = async () => {
    const currentChanges = activeTab === 'template' ? changedTemplateSettings : changedSettings;
    
    if (Object.keys(currentChanges).length === 0) {
      setSuccessMessage('Нет изменений для сохранения');
      return;
    }

    setSaving(true);
    setError('');

    try {
      if (activeTab === 'template') {
        // Сохраняем шаблонные настройки через Bot Templates API
        const updateData = {};
        Object.entries(changedTemplateSettings).forEach(([key, { value }]) => {
          updateData[key] = value;
        });

        const response = await fetch(`${API_BASE_URL}/api/bot-templates`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updateData),
        });

        if (!response.ok) {
          throw new Error('Ошибка сохранения шаблонных настроек');
        }

        setSuccessMessage(`Сохранено ${Object.keys(changedTemplateSettings).length} шаблонных настроек`);
        setChangedTemplateSettings({});
        await loadTemplateSettings();
      } else {
        // Сохраняем глобальные настройки
        const savePromises = Object.entries(changedSettings).map(async ([key, { value }]) => {
          const setting = settings.find(s => s.key === key);
          if (!setting) return;

          const response = await fetch(`${API_BASE_URL}/api/settings/${setting.id}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ value }),
          });

          if (!response.ok) {
            throw new Error(`Ошибка сохранения ${key}`);
          }

          return response.json();
        });

        await Promise.all(savePromises);
        
        setSuccessMessage(`Сохранено ${Object.keys(changedSettings).length} настроек`);
        setChangedSettings({});
        await loadSettings();
      }
    } catch (err) {
      setError('Ошибка сохранения: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  // Сброс изменений
  const handleResetChanges = () => {
    if (activeTab === 'template') {
      setChangedTemplateSettings({});
    } else {
      setChangedSettings({});
    }
    setSuccessMessage('Изменения сброшены');
  };

  // Загрузка при монтировании и смене таба
  useEffect(() => {
    if (activeTab === 'template') {
      loadTemplateSettings();
    } else {
      loadSettings();
    }
  }, [activeTab]);

  // Группировка настроек по категориям
  const currentSettings = getCurrentSettings();
  const groupedSettings = currentSettings.reduce((acc, setting) => {
    const category = setting.category || 'system';
    if (!acc[category]) acc[category] = [];
    acc[category].push(setting);
    return acc;
  }, {});

  // Получение текущего значения настройки (с учетом изменений)
  const getCurrentValue = (setting) => {
    const currentChanges = activeTab === 'template' ? changedTemplateSettings : changedSettings;
    return currentChanges[setting.key]?.value ?? setting.value;
  };

  // Подсчет изменений по категориям
  const getChangesCount = (category) => {
    const currentChanges = activeTab === 'template' ? changedTemplateSettings : changedSettings;
    return Object.keys(currentChanges).filter(key => {
      const setting = currentSettings.find(s => s.key === key);
      return setting && setting.category === category;
    }).length;
  };

  const currentChanges = activeTab === 'template' ? changedTemplateSettings : changedSettings;

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          AI и LLM Настройки
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Перезагрузить настройки">
            <IconButton onClick={activeTab === 'template' ? loadTemplateSettings : loadSettings} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Сбросить изменения">
            <IconButton 
              onClick={handleResetChanges} 
              disabled={Object.keys(currentChanges).length === 0}
            >
              <RestoreIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSaveAll}
            disabled={saving || Object.keys(currentChanges).length === 0}
            sx={{ ml: 1 }}
          >
            {saving ? 'Сохранение...' : `Сохранить (${Object.keys(currentChanges).length})`}
          </Button>
        </Box>
      </Box>

      {/* Табы */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          {Object.values(TABS_CONFIG).map((tab) => (
            <Tab
              key={tab.id}
              value={tab.id}
              label={tab.label}
              icon={tab.icon}
              iconPosition="start"
            />
          ))}
        </Tabs>
      </Box>

      {/* Описание текущего таба */}
      <Alert severity="info" sx={{ mb: 2 }}>
        {TABS_CONFIG[activeTab].description}
      </Alert>

      {/* Ошибки */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Информация об изменениях */}
      {Object.keys(currentChanges).length > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <InfoIcon />
            <Typography>
              Изменено настроек: {Object.keys(currentChanges).length}. 
              Не забудьте сохранить изменения.
            </Typography>
          </Box>
        </Alert>
      )}

      {/* Контент табов */}
      {activeTab === 'template' ? (
        <BotTemplateSettings />
      ) : (
        <>
          {/* Настройки по категориям */}
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
                {categorySettings.map((setting, index) => (
                  <Grid item xs={12} md={6} key={setting.key || index}>
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
                            {currentChanges[setting.key] && (
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
                          onChange={activeTab === 'template' ? handleTemplateSettingChange : handleSettingChange}
                          disabled={loading || saving}
                          isTemplate={activeTab === 'template'}
                        />
                        
                        {setting.value !== getCurrentValue(setting) && (
                          <Box sx={{ mt: 1, p: 1, bgcolor: 'warning.light', borderRadius: 1 }}>
                            <Typography variant="caption">
                              Было: {typeof setting.value === 'object' ? JSON.stringify(setting.value) : setting.value} → 
                              Будет: {typeof getCurrentValue(setting) === 'object' ? JSON.stringify(getCurrentValue(setting)) : getCurrentValue(setting)}
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
        </>
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