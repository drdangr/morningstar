import React from 'react';
import { Box, Typography, TextField, Alert } from '@mui/material';

const BotAISettings = ({ bot, onBotUpdate }) => {
  const handleChange = (field, value) => {
    if (onBotUpdate) {
      onBotUpdate({ ...bot, [field]: value });
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Alert severity="info" sx={{ mb: 2 }}>
        AI настройки готовы к использованию. 
        Настройте индивидуальные промпты для категоризации и суммаризации.
      </Alert>
      
      <Typography variant="h6" gutterBottom>
        AI Промпты и настройки
      </Typography>
      
      <TextField
        label="Промпт для категоризации"
        fullWidth
        multiline
        rows={4}
        value={bot?.categorization_prompt || ''}
        onChange={(e) => handleChange('categorization_prompt', e.target.value)}
        helperText="Инструкции для AI по категоризации постов этого бота"
      />
      
      <TextField
        label="Промпт для суммаризации"
        fullWidth
        multiline
        rows={4}
        value={bot?.summarization_prompt || ''}
        onChange={(e) => handleChange('summarization_prompt', e.target.value)}
        helperText="Инструкции для AI по генерации резюме (включая Tone of Voice)"
      />
      
      <Typography variant="body2" color="text.secondary">
        Через эти промпты вы можете настроить уникальный стиль и подход AI для каждого бота.
        Например, для "США Дайджест" - формальный стиль, для "Tech News" - технический жаргон.
      </Typography>
    </Box>
  );
};

export default BotAISettings; 