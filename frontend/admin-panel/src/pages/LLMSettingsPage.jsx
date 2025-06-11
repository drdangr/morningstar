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
  Snackbar
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Restore as RestoreIcon,
  Psychology as AIIcon,
  Settings as SystemIcon,
  Article as DigestIcon,
  Info as InfoIcon
} from '@mui/icons-material';

const API_BASE_URL = 'http://localhost:8000';

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

// Специальные компоненты для разных типов настроек
const SettingField = ({ setting, value, onChange, disabled }) => {
  const handleChange = (newValue) => {
    onChange(setting.key, newValue, setting.value_type);
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
          label={setting.key.replace(/_/g, ' ').toLowerCase()}
        />
      );

    case 'integer':
      return (
        <TextField
          fullWidth
          type="number"
          label={setting.key.replace(/_/g, ' ')}
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
          label={setting.key.replace(/_/g, ' ')}
          value={value || ''}
          onChange={(e) => handleChange(e.target.value)}
          disabled={disabled || !setting.is_editable}
          inputProps={{ min: 0, step: 0.1 }}
          helperText={setting.description}
        />
      );

    default: // string
      if (setting.key === 'AI_MODEL') {
        return (
          <FormControl fullWidth disabled={disabled || !setting.is_editable}>
            <InputLabel>AI Model</InputLabel>
            <Select
              value={value || ''}
              label="AI Model"
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

      if (setting.key === 'LOG_LEVEL') {
        return (
          <FormControl fullWidth disabled={disabled || !setting.is_editable}>
            <InputLabel>Log Level</InputLabel>
            <Select
              value={value || ''}
              label="Log Level"
              onChange={(e) => handleChange(e.target.value)}
            >
              <MenuItem value="DEBUG">DEBUG</MenuItem>
              <MenuItem value="INFO">INFO</MenuItem>
              <MenuItem value="WARNING">WARNING</MenuItem>
              <MenuItem value="ERROR">ERROR</MenuItem>
            </Select>
          </FormControl>
        );
      }

      return (
        <TextField
          fullWidth
          label={setting.key.replace(/_/g, ' ')}
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

  // Сохранение всех изменений
  const handleSaveAll = async () => {
    if (Object.keys(changedSettings).length === 0) {
      setSuccessMessage('Нет изменений для сохранения');
      return;
    }

    setSaving(true);
    setError('');

    try {
      // Сохраняем каждую измененную настройку
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
      await loadSettings(); // Перезагружаем настройки
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
          Settings
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