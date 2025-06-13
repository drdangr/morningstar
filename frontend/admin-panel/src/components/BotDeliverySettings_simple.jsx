import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Alert
} from '@mui/material';
import {
  Schedule as ScheduleIcon,
  Save as SaveIcon
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

const BotDeliverySettings = ({ bot, onBotUpdate }) => {
  const [deliverySchedule, setDeliverySchedule] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  console.log('🔍 BotDeliverySettings рендерится с bot:', bot);

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
        console.log('📊 Данные бота загружены:', botData);
        
        // Устанавливаем расписание доставки
        const schedule = botData.delivery_schedule || getDefaultSchedule();
        setDeliverySchedule(schedule);
      } else {
        throw new Error('Ошибка загрузки настроек бота');
      }
    } catch (err) {
      console.error('❌ Ошибка загрузки:', err);
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

  if (loading) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography>Загрузка настроек доставки...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Заголовок */}
      <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <ScheduleIcon />
        Настройки доставки дайджестов (Упрощенная версия)
      </Typography>
      
      <Typography variant="body2" color="textSecondary" gutterBottom>
        Настройте расписание доставки дайджестов для бота "{bot?.name}"
      </Typography>

      {/* Ошибки */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Информация о расписании */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Текущее расписание доставки
              </Typography>
              
              <Typography variant="body2" sx={{ mb: 2 }}>
                Всего доставок в неделю: <strong>{Object.values(deliverySchedule).reduce((total, times) => total + times.length, 0)}</strong>
              </Typography>
              
              {Object.entries(DAYS_OF_WEEK).map(([dayKey, dayName]) => (
                <Box key={dayKey} sx={{ mb: 1 }}>
                  <Typography variant="subtitle2">
                    {dayName}: {(deliverySchedule[dayKey] || []).join(', ') || 'Не запланировано'}
                  </Typography>
                </Box>
              ))}
              
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                sx={{ mt: 2 }}
                disabled
              >
                Сохранить (в разработке)
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default BotDeliverySettings; 