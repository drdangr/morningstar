import React from 'react';
import { Box, Typography, TextField, FormControl, InputLabel, Select, MenuItem } from '@mui/material';

const BotGeneralSettings = ({ bot, onBotUpdate }) => {
  const handleChange = (field, value) => {
    if (onBotUpdate) {
      onBotUpdate({ ...bot, [field]: value });
    }
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
      />
      
      <TextField
        label="Описание"
        fullWidth
        multiline
        rows={3}
        value={bot?.description || ''}
        onChange={(e) => handleChange('description', e.target.value)}
      />
      
      <TextField
        label="Telegram Bot Token"
        fullWidth
        value={bot?.bot_token || ''}
        onChange={(e) => handleChange('bot_token', e.target.value)}
      />
      
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
      />
    </Box>
  );
};

export default BotGeneralSettings; 