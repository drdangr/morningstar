import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  TextField, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Alert,
  CircularProgress,
  Chip
} from '@mui/material';
import apiService from '../services/api';

const BotGeneralSettings = ({ bot, onBotUpdate }) => {
  const [tokenValidation, setTokenValidation] = useState({
    status: null, // null, 'validating', 'valid', 'invalid'
    message: '',
    botInfo: null
  });
  
  const [debounceTimer, setDebounceTimer] = useState(null);

  // Debounced token validation
  useEffect(() => {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    
    const token = bot?.bot_token;
    if (token && token.length > 10) {
      const timer = setTimeout(() => {
        validateTokenAndUpdateBot(token);
      }, 1000); // 1 секунда задержки
      
      setDebounceTimer(timer);
    } else {
      setTokenValidation({
        status: null,
        message: '',
        botInfo: null
      });
    }
    
    return () => {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
    };
  }, [bot?.bot_token]);

  const validateTokenAndUpdateBot = async (token) => {
    setTokenValidation({
      status: 'validating',
      message: 'Проверка токена...',
      botInfo: null
    });

    try {
      const response = await apiService.post('/telegram-bot/validate-token', {
        bot_token: token
      });

      if (response.valid) {
        setTokenValidation({
          status: 'valid',
          message: 'Токен валиден',
          botInfo: response.bot_info
        });

        // Автоматически обновляем имя бота
        if (response.bot_info && response.bot_info.first_name) {
          handleChange('name', response.bot_info.first_name);
        }
      } else {
        setTokenValidation({
          status: 'invalid',
          message: response.error || 'Неверный токен',
          botInfo: null
        });
      }
    } catch (error) {
      setTokenValidation({
        status: 'invalid',
        message: `Ошибка при проверке токена: ${error.message}`,
        botInfo: null
      });
    }
  };

  const handleChange = (field, value) => {
    console.log('🔧 BotGeneralSettings.handleChange:', { field, value, currentBot: bot });
    if (onBotUpdate) {
      const updatedBot = { ...bot, [field]: value };
      console.log('📤 Calling onBotUpdate with:', updatedBot);
      onBotUpdate(updatedBot);
    }
  };

  const getTokenValidationColor = () => {
    switch (tokenValidation.status) {
      case 'valid':
        return 'success';
      case 'invalid':
        return 'error';
      case 'validating':
        return 'info';
      default:
        return 'default';
    }
  };

  const getTokenValidationIcon = () => {
    if (tokenValidation.status === 'validating') {
      return <CircularProgress size={16} />;
    }
    return null;
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Typography variant="h6" gutterBottom>
        Основные настройки бота
      </Typography>
      
      <TextField
        label="Название бота"
        fullWidth
        value={bot?.name || ''}
        onChange={(e) => handleChange('name', e.target.value)}
        helperText={tokenValidation.botInfo && tokenValidation.botInfo.first_name 
          ? `Имя из Telegram: ${tokenValidation.botInfo.first_name}` 
          : 'Имя будет автоматически обновлено при вводе токена'}
      />
      
      <TextField
        label="Описание"
        fullWidth
        multiline
        rows={3}
        value={bot?.description || ''}
        onChange={(e) => handleChange('description', e.target.value)}
      />
      
      <Box>
        <TextField
          label="Telegram Bot Token"
          fullWidth
          value={bot?.bot_token || ''}
          onChange={(e) => handleChange('bot_token', e.target.value)}
          helperText="Токен будет автоматически проверен через 1 секунду после ввода"
        />
        
        {tokenValidation.status && (
          <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              label={tokenValidation.message}
              color={getTokenValidationColor()}
              size="small"
              icon={getTokenValidationIcon()}
            />
            {tokenValidation.botInfo && (
              <Chip
                label={`@${tokenValidation.botInfo.username}`}
                color="primary"
                size="small"
                variant="outlined"
              />
            )}
          </Box>
        )}
        
        {tokenValidation.status === 'valid' && tokenValidation.botInfo && (
          <Alert severity="success" sx={{ mt: 1 }}>
            ✅ Бот найден: <strong>{tokenValidation.botInfo.first_name}</strong>
            {tokenValidation.botInfo.username && (
              <span> (@{tokenValidation.botInfo.username})</span>
            )}
          </Alert>
        )}
        
        {tokenValidation.status === 'invalid' && (
          <Alert severity="error" sx={{ mt: 1 }}>
            ❌ {tokenValidation.message}
          </Alert>
        )}
      </Box>
      
      <TextField
        label="Приветственное сообщение"
        fullWidth
        multiline
        rows={2}
        value={bot?.welcome_message || ''}
        onChange={(e) => handleChange('welcome_message', e.target.value)}
      />
      
      <FormControl fullWidth>
        <InputLabel>Язык по умолчанию</InputLabel>
        <Select
          value={bot?.default_language || 'ru'}
          onChange={(e) => handleChange('default_language', e.target.value)}
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
        value={bot?.max_posts_per_digest || 10}
        onChange={(e) => handleChange('max_posts_per_digest', parseInt(e.target.value))}
      />
      
      <TextField
        label="Максимальная длина резюме"
        type="number"
        fullWidth
        value={bot?.max_summary_length || 150}
        onChange={(e) => handleChange('max_summary_length', parseInt(e.target.value))}
        inputProps={{ min: 50, max: 2000 }}
        helperText="Диапазон: 50-2000 символов"
      />
    </Box>
  );
};

export default BotGeneralSettings; 