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
  SmartToy,
  Schedule as ScheduleIcon
} from '@mui/icons-material';

import BotTemplateSettings from '../components/BotTemplateSettings';

const API_BASE_URL = 'http://localhost:8000';

// Доступные модели OpenAI с характеристиками
const AVAILABLE_MODELS = {
  'gpt-4o-mini': {
    name: 'GPT-4o Mini',
    description: 'Быстрая и экономичная модель, идеальна для категоризации',
    cost_per_1k_tokens: 0.00015,
    speed: 'Быстро',
    quality: 'Высокое',
    recommended_for: ['categorization', 'analysis']
  },
  'gpt-4o': {
    name: 'GPT-4o',
    description: 'Высококачественная модель для сложных задач',
    cost_per_1k_tokens: 0.005,
    speed: 'Средне',
    quality: 'Очень высокое',
    recommended_for: ['summarization', 'complex_analysis']
  },
  'gpt-3.5-turbo': {
    name: 'GPT-3.5 Turbo',
    description: 'Быстрая модель для простых задач',
    cost_per_1k_tokens: 0.0005,
    speed: 'Очень быстро',
    quality: 'Среднее',
    recommended_for: ['simple_tasks']
  },
  'gpt-4': {
    name: 'GPT-4',
    description: 'Мощная модель для сложных задач (дорогая)',
    cost_per_1k_tokens: 0.03,
    speed: 'Медленно',
    quality: 'Максимальное',
    recommended_for: ['complex_reasoning']
  }
};

// AI Сервисы для которых можно выбирать модели
const AI_SERVICES = {
  categorization: {
    name: 'Категоризация',
    description: 'Определение категорий для постов',
    current_model: 'gpt-4o-mini',
    recommended_model: 'gpt-4o-mini',
    max_tokens: 1000,
    temperature: 0.3
  },
  summarization: {
    name: 'Суммаризация',
    description: 'Создание кратких резюме постов',
    current_model: 'gpt-4o',
    recommended_model: 'gpt-4o',
    max_tokens: 2000,
    temperature: 0.7
  },
  analysis: {
    name: 'Анализ',
    description: 'Глубокий анализ контента',
    current_model: 'gpt-4o-mini',
    recommended_model: 'gpt-4o-mini',
    max_tokens: 1500,
    temperature: 0.5
  }
};

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
  llm_models: {
    title: 'Выбор LLM Моделей',
    icon: <SmartToy />,
    color: 'warning',
    description: 'Настройка различных моделей для разных AI сервисов'
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

// Компонент для выбора LLM моделей для AI сервисов
const LLMModelSelector = ({ serviceKey, service, currentModel, onModelChange, onParameterChange, disabled }) => {
  const handleModelChange = (event) => {
    onModelChange(serviceKey, event.target.value);
  };

  const handleParameterChange = (paramName, value) => {
    onParameterChange(serviceKey, paramName, value);
  };

  const calculateMonthlyCost = (model) => {
    const modelInfo = AVAILABLE_MODELS[model];
    if (!modelInfo) return 0;
    
    // Примерная оценка: 1000 запросов в месяц, используем max_tokens сервиса
    const monthlyTokens = 1000 * (service.max_tokens || 500);
    return (monthlyTokens / 1000) * modelInfo.cost_per_1k_tokens;
  };

  return (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h6" gutterBottom>
              {service.name}
            </Typography>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              {service.description}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {service.recommended_model === currentModel && (
              <Chip label="Рекомендуемая" size="small" color="success" />
            )}
            <Chip 
              label={`~$${calculateMonthlyCost(currentModel).toFixed(3)}/мес`} 
              size="small" 
              color="info" 
            />
          </Box>
        </Box>

        <Grid container spacing={2}>
          {/* Выбор модели */}
          <Grid item xs={12}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Выберите модель</InputLabel>
              <Select
                value={currentModel}
                onChange={handleModelChange}
                disabled={disabled}
                label="Выберите модель"
              >
                {Object.entries(AVAILABLE_MODELS).map(([modelKey, modelInfo]) => (
                  <MenuItem key={modelKey} value={modelKey}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                      <Box>
                        <Typography variant="body1">{modelInfo.name}</Typography>
                        <Typography variant="caption" color="textSecondary">
                          {modelInfo.description}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                        <Chip label={modelInfo.speed} size="small" variant="outlined" />
                        <Chip label={modelInfo.quality} size="small" variant="outlined" />
                        <Typography variant="caption" color="primary">
                          ${modelInfo.cost_per_1k_tokens.toFixed(5)}/1k
                        </Typography>
                      </Box>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Настройки параметров */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Максимальное количество токенов"
              value={service.max_tokens || 1000}
              onChange={(e) => handleParameterChange('max_tokens', parseInt(e.target.value))}
              disabled={disabled}
              inputProps={{ min: 100, max: 8000, step: 100 }}
              helperText="От 100 до 8000 токенов"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Температура (креативность)"
              value={service.temperature || 0.5}
              onChange={(e) => handleParameterChange('temperature', parseFloat(e.target.value))}
              disabled={disabled}
              inputProps={{ min: 0, max: 2, step: 0.1 }}
              helperText="От 0.0 (точность) до 2.0 (креативность)"
            />
          </Grid>
        </Grid>

        {AVAILABLE_MODELS[currentModel] && (
          <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1, mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Характеристики выбранной модели:
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="textSecondary">Скорость</Typography>
                <Typography variant="body2">{AVAILABLE_MODELS[currentModel].speed}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="textSecondary">Качество</Typography>
                <Typography variant="body2">{AVAILABLE_MODELS[currentModel].quality}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="textSecondary">Стоимость/1k токенов</Typography>
                <Typography variant="body2">${AVAILABLE_MODELS[currentModel].cost_per_1k_tokens.toFixed(5)}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="textSecondary">Месячная оценка</Typography>
                <Typography variant="body2">${calculateMonthlyCost(currentModel).toFixed(3)}</Typography>
              </Grid>
            </Grid>
            
            <Box sx={{ mt: 2, p: 1, bgcolor: 'info.light', borderRadius: 1 }}>
              <Typography variant="caption" color="info.contrastText">
                💡 С текущими настройками: {service.max_tokens} токенов × температура {service.temperature}
              </Typography>
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
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
  
  // Состояние для LLM моделей
  const [llmModels, setLlmModels] = useState(AI_SERVICES);
  const [changedLlmModels, setChangedLlmModels] = useState({});

  // Обработчик изменения модели для AI сервиса
  const handleLlmModelChange = (serviceKey, newModel) => {
    setLlmModels(prev => ({
      ...prev,
      [serviceKey]: {
        ...prev[serviceKey],
        current_model: newModel
      }
    }));
    
    setChangedLlmModels(prev => ({
      ...prev,
      [`ai_${serviceKey}_model`]: newModel
    }));
  };

  // Обработчик изменения параметров AI сервиса
  const handleLlmParameterChange = (serviceKey, paramName, value) => {
    setLlmModels(prev => ({
      ...prev,
      [serviceKey]: {
        ...prev[serviceKey],
        [paramName]: value
      }
    }));
    
    setChangedLlmModels(prev => ({
      ...prev,
      [`ai_${serviceKey}_${paramName}`]: value.toString()
    }));
  };

  // Загрузка глобальных настроек
  const loadSettings = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/settings`);
      const data = await response.json();
      setSettings(data);
      
      // Загружаем LLM модели из системных переменных
      const llmModelSettings = {};
      Object.keys(AI_SERVICES).forEach(serviceKey => {
        const modelSetting = data.find(s => s.key === `ai_${serviceKey}_model`);
        const tokensSetting = data.find(s => s.key === `ai_${serviceKey}_max_tokens`);
        const tempSetting = data.find(s => s.key === `ai_${serviceKey}_temperature`);
        
        llmModelSettings[serviceKey] = {
          ...AI_SERVICES[serviceKey],
          current_model: modelSetting?.value || AI_SERVICES[serviceKey].current_model,
          max_tokens: tokensSetting ? parseInt(tokensSetting.value) : AI_SERVICES[serviceKey].max_tokens,
          temperature: tempSetting ? parseFloat(tempSetting.value) : AI_SERVICES[serviceKey].temperature
        };
      });
      
      setLlmModels(llmModelSettings);
      
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
        // AI Settings - оставляем только промпты
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
    
    // Для глобальных настроек фильтруем настройки AI категории
    // Показываем только нужные настройки, скрываем новые LLM переменные
    const filteredSettings = settings.filter(setting => {
      // Скрываем новые LLM переменные (управляются через аккордеон "Выбор LLM Моделей")
      const llmVariables = [
        'ai_categorization_model', 'ai_categorization_max_tokens', 'ai_categorization_temperature',
        'ai_summarization_model', 'ai_summarization_max_tokens', 'ai_summarization_temperature',
        'ai_analysis_model', 'ai_analysis_max_tokens', 'ai_analysis_temperature'
      ];
      
      if (llmVariables.includes(setting.key)) {
        return false;
      }
      
      // Для категории AI показываем только нужные настройки
      if (setting.category === 'ai') {
        const allowedAiSettings = ['MAX_POSTS_FOR_AI_ANALYSIS', 'MAX_SUMMARY_LENGTH'];
        return allowedAiSettings.includes(setting.key);
      }
      
      return true;
    });
    
    return filteredSettings;
  };

  // Сохранение всех изменений
  const handleSaveAll = async () => {
    const currentChanges = activeTab === 'template' ? changedTemplateSettings : changedSettings;
    const totalChanges = Object.keys(currentChanges).length + (activeTab === 'global' ? Object.keys(changedLlmModels).length : 0);
    
    if (totalChanges === 0) {
      setSuccessMessage('Нет изменений для сохранения');
      return;
    }

    setSaving(true);
    setError('');

    try {
      // Сохраняем изменения LLM моделей (только для глобального таба)
      if (activeTab === 'global' && Object.keys(changedLlmModels).length > 0) {
        const savePromises = Object.entries(changedLlmModels).map(async ([settingKey, newValue]) => {
          const setting = settings.find(s => s.key === settingKey);
          if (!setting) {
            console.warn(`Настройка ${settingKey} не найдена в БД`);
            return;
          }

          const response = await fetch(`${API_BASE_URL}/api/settings/${setting.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ value: newValue }),
          });

          if (!response.ok) {
            throw new Error(`Ошибка сохранения ${settingKey}`);
          }
          return response.json();
        });
        
        await Promise.all(savePromises);
        setChangedLlmModels({});
        console.log('✅ LLM настройки сохранены:', Object.keys(changedLlmModels));
      }

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
        if (Object.keys(changedSettings).length > 0) {
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
          setChangedSettings({});
          await loadSettings();
        }
        
        setSuccessMessage(`Сохранено ${totalChanges} изменений`);
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
      setChangedLlmModels({});
      // Сбрасываем LLM модели к исходному состоянию
      setLlmModels(AI_SERVICES);
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
  const totalChanges = Object.keys(currentChanges).length + (activeTab === 'global' ? Object.keys(changedLlmModels).length : 0);

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
              disabled={totalChanges === 0}
            >
              <RestoreIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSaveAll}
            disabled={saving || totalChanges === 0}
            sx={{ ml: 1 }}
          >
            {saving ? 'Сохранение...' : `Сохранить (${totalChanges})`}
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
      {totalChanges > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <InfoIcon />
            <Typography>
              Изменено настроек: {totalChanges}. 
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
        
        // Специальная обработка для категории LLM Models
        if (categoryKey === 'llm_models') {
          const llmChangesCount = Object.keys(changedLlmModels).length;
          
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
                      label={`${Object.keys(AI_SERVICES).length} сервисов`} 
                      size="small" 
                      color={categoryConfig.color}
                      variant="outlined"
                    />
                    {llmChangesCount > 0 && (
                      <Chip 
                        label={`${llmChangesCount} изменений`} 
                        size="small" 
                        color="warning"
                      />
                    )}
                  </Box>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ mb: 2 }}>
                  <Alert severity="info">
                    Выберите оптимальные модели для каждого AI сервиса. 
                    Рекомендации основаны на реальных тестах производительности и стоимости.
                  </Alert>
                </Box>
                
                {Object.entries(llmModels).map(([serviceKey, service]) => (
                  <LLMModelSelector
                    key={serviceKey}
                    serviceKey={serviceKey}
                    service={service}
                    currentModel={service.current_model}
                    onModelChange={handleLlmModelChange}
                    onParameterChange={handleLlmParameterChange}
                    disabled={loading || saving}
                  />
                ))}
                
                {llmChangesCount > 0 && (
                  <Box sx={{ mt: 2, p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Планируемые изменения:
                    </Typography>
                    {Object.entries(changedLlmModels).map(([serviceKey, newModel]) => (
                      <Typography key={serviceKey} variant="body2">
                        • {AI_SERVICES[serviceKey].name}: {AI_SERVICES[serviceKey].current_model} → {newModel}
                      </Typography>
                    ))}
                  </Box>
                )}
              </AccordionDetails>
            </Accordion>
          );
        }
        
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