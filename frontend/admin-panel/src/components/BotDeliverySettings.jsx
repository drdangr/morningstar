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
  Divider
} from '@mui/material';
import {
  Schedule as ScheduleIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  AccessTime as TimeIcon,
  Public as TimezoneIcon,
  Restore as RestoreIcon
} from '@mui/icons-material';

const DAYS_OF_WEEK = {
  monday: 'Понедельник',
  tuesday: 'Вторник', 
  wednesday: 'Среда',
  thursday: 'Четверг',
  friday: 'Пятница',
  saturday: 'Суббота',
  sunday: 'Воскресенье'
};

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

const BotDeliverySettings = ({ bot, onBotUpdate }) => {
  console.log('🔍 BotDeliverySettings начинает рендериться с bot:', bot);
  
  const [deliverySchedule, setDeliverySchedule] = useState({});
  const [timezone, setTimezone] = useState('Europe/Moscow');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [hasChanges, setHasChanges] = useState(false);
  
  console.log('🔍 State инициализирован, deliverySchedule:', deliverySchedule);

  // Загрузка настроек при монтировании
  useEffect(() => {
    if (bot) {
      loadBotDeliverySettings();
    }
  }, [bot?.id]);

  const loadBotDeliverySettings = async () => {
    if (!bot?.id) return;

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`http://localhost:8000/api/public-bots/${bot.id}`);
      if (response.ok) {
        const botData = await response.json();
        
        // Устанавливаем расписание доставки
        const schedule = botData.delivery_schedule || getDefaultSchedule();
        
        // Преобразуем сложную структуру API в простые массивы времен
        const simplifiedSchedule = {};
        Object.entries(schedule).forEach(([day, dayData]) => {
          if (Array.isArray(dayData)) {
            // Уже простой массив времен
            simplifiedSchedule[day] = dayData;
          } else if (dayData && dayData.times && Array.isArray(dayData.times)) {
            // Сложная структура с объектами времен
            simplifiedSchedule[day] = dayData.times.map(timeObj => timeObj.time || timeObj);
          } else if (dayData && typeof dayData === 'object') {
            // Попытка извлечь времена из объекта
            const times = Object.values(dayData).filter(val => 
              typeof val === 'string' && val.match(/^\d{2}:\d{2}$/)
            );
            if (times.length > 0) {
              simplifiedSchedule[day] = times;
            }
          }
        });
        
        console.log('📊 Преобразованное расписание:', simplifiedSchedule);
        setDeliverySchedule(simplifiedSchedule);
        
        // Устанавливаем часовой пояс
        setTimezone(botData.timezone || 'Europe/Moscow');
        
        setHasChanges(false);
      } else {
        throw new Error('Ошибка загрузки настроек бота');
      }
    } catch (err) {
      setError('Ошибка загрузки настроек доставки: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const getDefaultSchedule = () => {
    return {
      monday: ['08:00', '19:00'],
      tuesday: ['08:00', '19:00'],
      wednesday: ['08:00', '19:00'],
      thursday: ['08:00', '19:00'],
      friday: ['08:00', '19:00'],
      saturday: ['10:00'],
      sunday: ['10:00']
    };
  };

  const handleScheduleChange = (day, timeIndex, newTime) => {
    setDeliverySchedule(prev => {
      const newSchedule = { ...prev };
      if (!newSchedule[day]) {
        newSchedule[day] = [];
      }
      newSchedule[day] = [...newSchedule[day]];
      newSchedule[day][timeIndex] = newTime;
      return newSchedule;
    });
    setHasChanges(true);
  };

  const addTimeSlot = (day) => {
    setDeliverySchedule(prev => {
      const newSchedule = { ...prev };
      if (!newSchedule[day]) {
        newSchedule[day] = [];
      }
      newSchedule[day] = [...newSchedule[day], '12:00'];
      return newSchedule;
    });
    setHasChanges(true);
  };

  const removeTimeSlot = (day, timeIndex) => {
    setDeliverySchedule(prev => {
      const newSchedule = { ...prev };
      if (newSchedule[day]) {
        newSchedule[day] = newSchedule[day].filter((_, index) => index !== timeIndex);
        if (newSchedule[day].length === 0) {
          delete newSchedule[day];
        }
      }
      return newSchedule;
    });
    setHasChanges(true);
  };

  const handleTimezoneChange = (newTimezone) => {
    setTimezone(newTimezone);
    setHasChanges(true);
  };

  const saveDeliverySettings = async () => {
    if (!bot?.id) return;

    setSaving(true);
    setError('');

    try {
      const updateData = {
        delivery_schedule: deliverySchedule,
        timezone: timezone
      };

      const response = await fetch(`http://localhost:8000/api/public-bots/${bot.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });

      if (response.ok) {
        const updatedBot = await response.json();
        setSuccessMessage('Настройки доставки сохранены успешно');
        setHasChanges(false);
        
        if (onBotUpdate) {
          onBotUpdate(updatedBot);
        }
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

  const resetToDefault = () => {
    setDeliverySchedule(getDefaultSchedule());
    setTimezone('Europe/Moscow');
    setHasChanges(true);
  };

  const loadFromTemplate = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/bot-templates');
      if (response.ok) {
        const template = await response.json();
        setDeliverySchedule(template.default_delivery_schedule || getDefaultSchedule());
        setTimezone(template.default_timezone || 'Europe/Moscow');
        setHasChanges(true);
        setSuccessMessage('Настройки загружены из шаблона');
      } else {
        throw new Error('Ошибка загрузки шаблона');
      }
    } catch (err) {
      setError('Ошибка загрузки шаблона: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const getTotalDeliveries = () => {
    return Object.values(deliverySchedule).reduce((total, times) => total + times.length, 0);
  };

  console.log('🔍 Перед рендерингом: loading=', loading, 'error=', error);

  if (loading) {
    console.log('🔍 Рендерим loading состояние');
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography>Загрузка настроек доставки...</Typography>
      </Box>
    );
  }

  console.log('🔍 Начинаем рендерить основной компонент');
  
  return (
    <Box sx={{ p: 3 }}>
      {/* Заголовок и действия */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ScheduleIcon />
            Настройки доставки дайджестов
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Настройте расписание доставки дайджестов для бота "{bot?.name}"
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Загрузить из шаблона">
            <IconButton onClick={loadFromTemplate} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Сбросить к значениям по умолчанию">
            <IconButton onClick={resetToDefault}>
              <RestoreIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={saveDeliverySettings}
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

      {/* Компактная панель с общими настройками и статистикой */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <FormControl fullWidth size="small">
            <InputLabel>Часовой пояс</InputLabel>
            <Select
              value={timezone}
              onChange={(e) => handleTimezoneChange(e.target.value)}
              label="Часовой пояс"
            >
              {COMMON_TIMEZONES.map((tz) => (
                <MenuItem key={tz} value={tz}>
                  {tz}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, bgcolor: 'primary.50', border: '1px solid', borderColor: 'primary.200' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" color="primary.main" sx={{ fontWeight: 'medium' }}>
                  📊 Всего доставок в неделю:
                </Typography>
                <Typography variant="h6" color="primary.main" sx={{ fontWeight: 'bold' }}>
                  {getTotalDeliveries()}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" color="primary.main" sx={{ fontWeight: 'medium' }}>
                  📅 Активных дней:
                </Typography>
                <Typography variant="h6" color="primary.main" sx={{ fontWeight: 'bold' }}>
                  {Object.keys(deliverySchedule).length}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" color="primary.main" sx={{ fontWeight: 'medium' }}>
                  🌍 Часовой пояс:
                </Typography>
                <Typography variant="body2" color="primary.main" sx={{ fontWeight: 'bold' }}>
                  {timezone}
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Расписание по дням недели */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TimeIcon />
                Расписание доставки по дням недели
              </Typography>
              
              {Object.entries(DAYS_OF_WEEK).map(([dayKey, dayName]) => (
                <Box key={dayKey} sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="h6" sx={{ fontWeight: 'medium', color: 'text.primary' }}>
                      {dayName}
                    </Typography>
                    <Button
                      size="small"
                      startIcon={<AddIcon />}
                      onClick={() => addTimeSlot(dayKey)}
                      variant="outlined"
                      color="primary"
                    >
                      Добавить время
                    </Button>
                  </Box>
                  
                  {(deliverySchedule[dayKey] && deliverySchedule[dayKey].length > 0) ? (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                      {deliverySchedule[dayKey].map((time, timeIndex) => (
                        <Paper 
                          key={timeIndex} 
                          sx={{ 
                            p: 1.5, 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: 1,
                            bgcolor: 'background.paper',
                            border: '1px solid',
                            borderColor: 'divider',
                            borderRadius: 2
                          }}
                        >
                          <TextField
                            type="time"
                            value={time}
                            onChange={(e) => handleScheduleChange(dayKey, timeIndex, e.target.value)}
                            size="small"
                            variant="outlined"
                            sx={{ 
                              width: 130,
                              '& .MuiOutlinedInput-root': {
                                height: 36
                              }
                            }}
                          />
                          <IconButton
                            size="small"
                            onClick={() => removeTimeSlot(dayKey, timeIndex)}
                            color="error"
                            sx={{ 
                              '&:hover': { 
                                bgcolor: 'error.50' 
                              }
                            }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Paper>
                      ))}
                    </Box>
                  ) : (
                    <Paper sx={{ 
                      p: 2, 
                      bgcolor: 'grey.50', 
                      border: '1px dashed', 
                      borderColor: 'grey.300',
                      textAlign: 'center'
                    }}>
                      <Typography variant="body2" color="textSecondary" sx={{ fontStyle: 'italic' }}>
                        📭 Доставка не запланирована
                      </Typography>
                    </Paper>
                  )}
                  
                  {dayKey !== 'sunday' && <Divider sx={{ mt: 2 }} />}
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default BotDeliverySettings; 