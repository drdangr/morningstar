import React from 'react';
import { Box, Typography } from '@mui/material';

const BotDeliverySettings = ({ bot, onBotUpdate }) => {
  console.log('🔍 BotDeliverySettings рендерится с bot:', bot);
  
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5">
        🧪 Тест компонента настроек доставки
      </Typography>
      <Typography variant="body1">
        Бот: {bot?.name || 'НЕ ВЫБРАН'}
      </Typography>
      <Typography variant="body2">
        ID: {bot?.id || 'НЕТ ID'}
      </Typography>
      <Typography variant="body2" color="success.main">
        ✅ Компонент загружается успешно!
      </Typography>
    </Box>
  );
};

export default BotDeliverySettings; 