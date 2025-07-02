import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Tooltip,
  Badge
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Psychology as AIIcon,
  Speed as PerformanceIcon,
  AttachMoney as CostIcon,
  ExpandMore as ExpandMoreIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  Memory as MemoryIcon,
  Timer as TimerIcon,
  CompareArrows as CompareIcon
} from '@mui/icons-material';
import apiService from '../services/api';

/**
 * LLM Settings Page v5 - Выбор разных моделей для разных сервисов
 * Task 2.1: Добавить выбор разных LLM для разных сервисов
 */

// Конфигурация AI сервисов
const AI_SERVICES = {
  categorization: {
    name: 'Категоризация',
    description: 'Определение тематики и категории постов',
    icon: <AIIcon />,
    color: 'primary',
    recommended_models: ['gpt-4o-mini', 'gpt-3.5-turbo'],
    priority: 'speed' // speed, quality, balance
  },
  summarization: {
    name: 'Суммаризация',
    description: 'Создание кратких резюме постов',
    icon: <MemoryIcon />,
    color: 'secondary',
    recommended_models: ['gpt-4o', 'gpt-4'],
    priority: 'quality'
  },
  analysis: {
    name: 'Анализ важности',
    description: 'Оценка важности и релевантности',
    icon: <TrendingUpIcon />,
    color: 'success',
    recommended_models: ['gpt-4o-mini', 'gpt-4o'],
    priority: 'balance'
  }
};

// Моделы с их характеристиками (из нашего анализатора)
const MODEL_SPECS = {
  'gpt-4o-mini': {
    provider: 'OpenAI',
    input_price: 0.15,
    output_price: 0.60,
    context_window: 128000,
    speed: 'fast',
    quality: 'good',
    category: 'budget',
    description: 'Быстрая и дешёвая, хорошее качество'
  },
  'gpt-4o': {
    provider: 'OpenAI',
    input_price: 2.50,
    output_price: 10.00,
    context_window: 128000,
    speed: 'fast',
    quality: 'excellent',
    category: 'flagship',
    description: 'Мультимодальная, быстрая, оптимальная'
  },
  'gpt-3.5-turbo': {
    provider: 'OpenAI',
    input_price: 0.50,
    output_price: 1.50,
    context_window: 16385,
    speed: 'very_fast',
    quality: 'good',
    category: 'budget',
    description: 'Базовая, бюджетная'
  },
  'gpt-4': {
    provider: 'OpenAI',
    input_price: 30.00,
    output_price: 60.00,
    context_window: 8192,
    speed: 'medium',
    quality: 'excellent',
    category: 'premium',
    description: 'Умная модель с небольшим контекстом'
  }
};

function LLMSettingsPage() {
  const [activeTab, setActiveTab] = useState('services');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  
  // Состояние настроек LLM
  const [llmSettings, setLlmSettings] = useState({});
  const [availableModels, setAvailableModels] = useState([]);
  const [modelComparison, setModelComparison] = useState(null);
  const [costAnalysis, setCostAnalysis] = useState(null);
  
  // Диалоги
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingService, setEditingService] = useState(null);
  const [comparisonDialogOpen, setComparisonDialogOpen] = useState(false);

  useEffect(() => {
    loadLLMSettings();
    loadAvailableModels();
  }, []);

  const loadLLMSettings = async () => {
    setLoading(true);
    try {
      // Пока используем mock данные
      const mockSettings = {
        categorization: { model_name: 'gpt-4o-mini', max_tokens: 2000, temperature: 0.3 },
        summarization: { model_name: 'gpt-4o', max_tokens: 4000, temperature: 0.7 },
        analysis: { model_name: 'gpt-4o-mini', max_tokens: 1500, temperature: 0.5 }
      };
      setLlmSettings(mockSettings);
      
      // Mock анализ стоимости
      const mockCostAnalysis = {
        categorization: { avg_input_tokens: 800, avg_output_tokens: 200, monthly_requests: 5000 },
        summarization: { avg_input_tokens: 1200, avg_output_tokens: 800, monthly_requests: 3000 },
        analysis: { avg_input_tokens: 600, avg_output_tokens: 300, monthly_requests: 2000 }
      };
      setCostAnalysis(mockCostAnalysis);
      
    } catch (err) {
      setError('Ошибка загрузки настроек LLM: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableModels = async () => {
    try {
      // Mock данные доступных моделей
      setAvailableModels(Object.keys(MODEL_SPECS));
    } catch (err) {
      console.error('Ошибка загрузки моделей:', err);
    }
  };

  const handleServiceModelChange = async (serviceKey, modelName) => {
    setSaving(true);
    try {
      // Mock обновление
      setLlmSettings(prev => ({
        ...prev,
        [serviceKey]: {
          ...prev[serviceKey],
          model_name: modelName
        }
      }));
      
      setSuccessMessage(`Модель для ${AI_SERVICES[serviceKey].name} обновлена на ${modelName}`);
      
    } catch (err) {
      setError('Ошибка обновления настроек: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const runModelComparison = async () => {
    setLoading(true);
    try {
      // Mock сравнение моделей
      const mockComparison = {
        categorization: {
          'gpt-4o-mini': { accuracy: 0.92, speed: 1.2, cost: 0.001 },
          'gpt-3.5-turbo': { accuracy: 0.88, speed: 0.8, cost: 0.0008 },
          'gpt-4o': { accuracy: 0.95, speed: 1.1, cost: 0.005 }
        },
        summarization: {
          'gpt-4o': { quality: 0.96, speed: 1.3, cost: 0.008 },
          'gpt-4': { quality: 0.94, speed: 0.9, cost: 0.025 },
          'gpt-4o-mini': { quality: 0.89, speed: 1.4, cost: 0.002 }
        }
      };
      setModelComparison(mockComparison);
      setComparisonDialogOpen(true);
    } catch (err) {
      setError('Ошибка сравнения моделей: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const getModelBadgeColor = (category) => {
    switch (category) {
      case 'budget': return 'success';
      case 'flagship': return 'primary';
      case 'premium': return 'warning';
      default: return 'default';
    }
  };

  const getSpeedIcon = (speed) => {
    switch (speed) {
      case 'very_fast': return '🚀';
      case 'fast': return '⚡';
      case 'medium': return '🏃';
      case 'slow': return '🐌';
      default: return '⏱️';
    }
  };

  const getQualityStars = (quality) => {
    switch (quality) {
      case 'excellent': return '⭐⭐⭐⭐⭐';
      case 'very_good': return '⭐⭐⭐⭐';
      case 'good': return '⭐⭐⭐';
      case 'fair': return '⭐⭐';
      default: return '⭐';
    }
  };

  const calculateServiceCost = (serviceKey, modelName) => {
    if (!costAnalysis || !costAnalysis[serviceKey]) return null;
    
    const serviceData = costAnalysis[serviceKey];
    const modelData = MODEL_SPECS[modelName];
    
    if (!modelData) return null;
    
    const avgTokensInput = serviceData.avg_input_tokens || 1000;
    const avgTokensOutput = serviceData.avg_output_tokens || 500;
    
    const inputCost = (avgTokensInput / 1_000_000) * modelData.input_price;
    const outputCost = (avgTokensOutput / 1_000_000) * modelData.output_price;
    
    return {
      per_request: inputCost + outputCost,
      per_1k_requests: (inputCost + outputCost) * 1000,
      monthly_estimate: (inputCost + outputCost) * (serviceData.monthly_requests || 1000)
    };
  };

  // Компонент карточки сервиса
  const ServiceCard = ({ serviceKey, serviceConfig }) => {
    const currentModel = llmSettings[serviceKey]?.model_name || 'gpt-4o-mini';
    const modelSpec = MODEL_SPECS[currentModel];
    const cost = calculateServiceCost(serviceKey, currentModel);

    return (
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Box display="flex" alignItems="center" mb={2}>
            {serviceConfig.icon}
            <Box ml={2}>
              <Typography variant="h6">{serviceConfig.name}</Typography>
              <Typography variant="body2" color="text.secondary">
                {serviceConfig.description}
              </Typography>
            </Box>
          </Box>

          <Box mb={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Модель</InputLabel>
              <Select
                value={currentModel}
                label="Модель"
                onChange={(e) => handleServiceModelChange(serviceKey, e.target.value)}
                disabled={saving}
              >
                {Object.keys(MODEL_SPECS).map(modelName => (
                  <MenuItem key={modelName} value={modelName}>
                    <Box display="flex" alignItems="center" width="100%">
                      <Typography variant="body2" sx={{ flexGrow: 1 }}>
                        {modelName}
                      </Typography>
                      <Chip 
                        label={MODEL_SPECS[modelName].category}
                        size="small"
                        color={getModelBadgeColor(MODEL_SPECS[modelName].category)}
                        sx={{ ml: 1 }}
                      />
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {modelSpec && (
            <Box>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2" color="text.secondary">
                  Скорость: {getSpeedIcon(modelSpec.speed)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Качество: {getQualityStars(modelSpec.quality)}
                </Typography>
              </Box>
              
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2" color="text.secondary">
                  Контекст: {modelSpec.context_window.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Провайдер: {modelSpec.provider}
                </Typography>
              </Box>

              {cost && (
                <Box mt={2} p={1} bgcolor="grey.100" borderRadius={1}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    💰 Стоимость:
                  </Typography>
                  <Typography variant="body2">
                    За запрос: ${cost.per_request.toFixed(6)}
                  </Typography>
                  <Typography variant="body2">
                    В месяц: ${cost.monthly_estimate.toFixed(2)}
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </CardContent>

        <CardActions>
          <Button 
            size="small" 
            onClick={() => {
              setEditingService(serviceKey);
              setEditDialogOpen(true);
            }}
            startIcon={<EditIcon />}
          >
            Настроить
          </Button>
        </CardActions>
      </Card>
    );
  };

  // Компонент таблицы сравнения моделей
  const ModelsComparisonTable = () => (
    <TableContainer component={Paper}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Модель</TableCell>
            <TableCell>Категория</TableCell>
            <TableCell>Скорость</TableCell>
            <TableCell>Качество</TableCell>
            <TableCell>Контекст</TableCell>
            <TableCell>Цена вход</TableCell>
            <TableCell>Цена выход</TableCell>
            <TableCell>Рекомендуется для</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {Object.entries(MODEL_SPECS).map(([modelName, spec]) => (
            <TableRow key={modelName}>
              <TableCell>
                <Typography variant="body2" fontWeight="bold">
                  {modelName}
                </Typography>
              </TableCell>
              <TableCell>
                <Chip 
                  label={spec.category}
                  size="small"
                  color={getModelBadgeColor(spec.category)}
                />
              </TableCell>
              <TableCell>{getSpeedIcon(spec.speed)}</TableCell>
              <TableCell>{getQualityStars(spec.quality)}</TableCell>
              <TableCell>{spec.context_window.toLocaleString()}</TableCell>
              <TableCell>${spec.input_price}/1M</TableCell>
              <TableCell>${spec.output_price}/1M</TableCell>
              <TableCell>
                <Box>
                  {Object.entries(AI_SERVICES)
                    .filter(([, config]) => config.recommended_models.includes(modelName))
                    .map(([serviceKey, config]) => (
                      <Chip 
                        key={serviceKey}
                        label={config.name}
                        size="small"
                        variant="outlined"
                        sx={{ mr: 0.5, mb: 0.5 }}
                      />
                    ))
                  }
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  return (
    <Box p={3}>
      <Box mb={3}>
        <Typography variant="h4" gutterBottom>
          <SettingsIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
          Настройки LLM Моделей
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Выбор разных моделей для разных AI сервисов
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {successMessage && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccessMessage('')}>
          {successMessage}
        </Alert>
      )}

      <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="Сервисы AI" value="services" />
        <Tab label="Сравнение моделей" value="comparison" />
        <Tab label="Анализ стоимости" value="cost" />
      </Tabs>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {activeTab === 'services' && (
        <Box>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h6">
              Настройка моделей по сервисам
            </Typography>
            <Box>
              <Button
                variant="outlined"
                startIcon={<CompareIcon />}
                onClick={runModelComparison}
                disabled={loading}
                sx={{ mr: 1 }}
              >
                Сравнить модели
              </Button>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={loadLLMSettings}
                disabled={loading}
              >
                Обновить
              </Button>
            </Box>
          </Box>

          <Grid container spacing={3}>
            {Object.entries(AI_SERVICES).map(([serviceKey, serviceConfig]) => (
              <Grid item xs={12} md={4} key={serviceKey}>
                <ServiceCard serviceKey={serviceKey} serviceConfig={serviceConfig} />
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {activeTab === 'comparison' && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Сравнение доступных моделей
          </Typography>
          <ModelsComparisonTable />
        </Box>
      )}

      {activeTab === 'cost' && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Анализ стоимости
          </Typography>
          
          {costAnalysis && (
            <Grid container spacing={3}>
              {Object.entries(AI_SERVICES).map(([serviceKey, serviceConfig]) => {
                const currentModel = llmSettings[serviceKey]?.model_name || 'gpt-4o-mini';
                const cost = calculateServiceCost(serviceKey, currentModel);
                
                return (
                  <Grid item xs={12} md={4} key={serviceKey}>
                    <Card>
                      <CardContent>
                        <Box display="flex" alignItems="center" mb={2}>
                          {serviceConfig.icon}
                          <Typography variant="h6" sx={{ ml: 1 }}>
                            {serviceConfig.name}
                          </Typography>
                        </Box>
                        
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Модель: {currentModel}
                        </Typography>
                        
                        {cost && (
                          <Box>
                            <Typography variant="body2">
                              За запрос: ${cost.per_request.toFixed(6)}
                            </Typography>
                            <Typography variant="body2">
                              За 1000 запросов: ${cost.per_1k_requests.toFixed(4)}
                            </Typography>
                            <Typography variant="body2" fontWeight="bold">
                              Месячная оценка: ${cost.monthly_estimate.toFixed(2)}
                            </Typography>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          )}
        </Box>
      )}

      {/* Диалог редактирования сервиса */}
      <Dialog 
        open={editDialogOpen} 
        onClose={() => setEditDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Настройка сервиса: {editingService && AI_SERVICES[editingService]?.name}
        </DialogTitle>
        <DialogContent>
          {editingService && (
            <Box pt={1}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {AI_SERVICES[editingService].description}
              </Typography>
              
              <FormControl fullWidth sx={{ mt: 2 }}>
                <InputLabel>Модель</InputLabel>
                <Select
                  value={llmSettings[editingService]?.model_name || 'gpt-4o-mini'}
                  label="Модель"
                  onChange={(e) => handleServiceModelChange(editingService, e.target.value)}
                >
                  {Object.keys(MODEL_SPECS).map(modelName => (
                    <MenuItem key={modelName} value={modelName}>
                      {modelName} - {MODEL_SPECS[modelName].description}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              {/* Дополнительные настройки */}
              <TextField
                fullWidth
                label="Максимум токенов"
                type="number"
                value={llmSettings[editingService]?.max_tokens || 4000}
                sx={{ mt: 2 }}
              />
              
              <TextField
                fullWidth
                label="Температура"
                type="number"
                inputProps={{ min: 0, max: 2, step: 0.1 }}
                value={llmSettings[editingService]?.temperature || 0.3}
                sx={{ mt: 2 }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>
            Отмена
          </Button>
          <Button 
            variant="contained" 
            onClick={() => setEditDialogOpen(false)}
            startIcon={<SaveIcon />}
          >
            Сохранить
          </Button>
        </DialogActions>
      </Dialog>

      {/* Диалог сравнения моделей */}
      <Dialog 
        open={comparisonDialogOpen} 
        onClose={() => setComparisonDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Результаты сравнения моделей</DialogTitle>
        <DialogContent>
          {modelComparison && (
            <Box>
              {Object.entries(modelComparison).map(([serviceKey, results]) => (
                <Box key={serviceKey} mb={3}>
                  <Typography variant="h6" gutterBottom>
                    {AI_SERVICES[serviceKey].name}
                  </Typography>
                  <TableContainer component={Paper} sx={{ mb: 2 }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Модель</TableCell>
                          <TableCell>Точность/Качество</TableCell>
                          <TableCell>Скорость (сек)</TableCell>
                          <TableCell>Стоимость ($)</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {Object.entries(results).map(([model, metrics]) => (
                          <TableRow key={model}>
                            <TableCell>{model}</TableCell>
                            <TableCell>
                              {((metrics.accuracy || metrics.quality) * 100).toFixed(1)}%
                            </TableCell>
                            <TableCell>{metrics.speed.toFixed(1)}</TableCell>
                            <TableCell>${metrics.cost.toFixed(6)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              ))}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setComparisonDialogOpen(false)}>
            Закрыть
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default LLMSettingsPage; 