import React, { useState, useEffect } from 'react';
import {
  Box,
  Tabs,
  Tab,
  Typography,
  Paper
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Tv as ChannelsIcon,
  Category as CategoriesIcon,
  Psychology as AIIcon
} from '@mui/icons-material';

import BotChannelsManager from './BotChannelsManager';
import BotCategoriesManager from './BotCategoriesManager';
import BotAISettings from './BotAISettings';
import BotGeneralSettings from './BotGeneralSettings';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`bot-config-tabpanel-${index}`}
      aria-labelledby={`bot-config-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const BotConfigurationTabs = ({ bot, onBotUpdate, onClose }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [botChannels, setBotChannels] = useState([]);
  const [botCategories, setBotCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [priorityChanges, setPriorityChanges] = useState({}); // Отслеживаем изменения приоритетов

  // Загружаем данные каналов и категорий при изменении бота
  useEffect(() => {
    if (bot?.id) {
      loadBotData();
    }
  }, [bot?.id]);

  const loadBotData = async () => {
    if (!bot?.id) return;
    
    setLoading(true);
    try {
      // Загружаем каналы бота
      const channelsResponse = await fetch(`http://localhost:8000/api/public-bots/${bot.id}/channels`);
      if (channelsResponse.ok) {
        const channels = await channelsResponse.json();
        setBotChannels(channels);
      }

      // Загружаем категории бота
      const categoriesResponse = await fetch(`http://localhost:8000/api/public-bots/${bot.id}/categories`);
      if (categoriesResponse.ok) {
        const categories = await categoriesResponse.json();
        // Добавляем приоритеты для отображения
        const categoriesWithPriority = categories.map((cat, index) => ({
          ...cat,
          name: cat.category_name || cat.name, // Трансформация для совместимости
          priority: index + 1
        }));
        setBotCategories(categoriesWithPriority);
      }
    } catch (error) {
      console.error('Ошибка загрузки данных бота:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleChannelsChange = (newChannels) => {
    setBotChannels(newChannels);
    if (onBotUpdate) {
      onBotUpdate({ ...bot, channels: newChannels });
    }
  };

  const handleCategoriesChange = (newCategories) => {
    setBotCategories(newCategories);
    if (onBotUpdate) {
      onBotUpdate({ ...bot, categories: newCategories });
    }
  };

  // Обработка изменения приоритета категории
  const handlePriorityChange = (categoryId, newPriority) => {
    console.log(`📝 Запоминаем изменение приоритета: категория ${categoryId}, приоритет ${newPriority}`);
    setPriorityChanges(prev => ({
      ...prev,
      [categoryId]: newPriority
    }));
  };

  // Функция сохранения изменений приоритетов
  const savePriorityChanges = async () => {
    const changesToSave = Object.keys(priorityChanges);
    if (changesToSave.length === 0) return;

    console.log(`💾 Сохраняем изменения приоритетов при закрытии:`, priorityChanges);

    try {
      // Сохраняем все изменения параллельно
      const savePromises = changesToSave.map(async (categoryId) => {
        const newPriority = priorityChanges[categoryId];
        
        const response = await fetch(`http://localhost:8000/api/public-bots/${bot.id}/categories/${categoryId}/priority`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            priority: parseFloat(newPriority)
          })
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(`Ошибка сохранения категории ${categoryId}: ${errorData.detail}`);
        }

        return { categoryId, newPriority };
      });

      await Promise.all(savePromises);
      console.log(`✅ Все изменения приоритетов сохранены`);
      
      // Очищаем изменения после успешного сохранения
      setPriorityChanges({});
      
    } catch (error) {
      console.error('Ошибка сохранения приоритетов:', error);
      // Можно показать уведомление об ошибке
    }
  };

  // Сохранение при размонтировании компонента
  useEffect(() => {
    return () => {
      if (Object.keys(priorityChanges).length > 0) {
        savePriorityChanges();
      }
    };
  }, [priorityChanges]);

  if (!bot) {
    return (
      <Typography variant="body2" color="text.secondary">
        Выберите бота для настройки
      </Typography>
    );
  }

  return (
    <Paper sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{
            '& .MuiTab-root': {
              minHeight: 64,
              textTransform: 'none',
              fontSize: '1rem'
            }
          }}
        >
          <Tab 
            icon={<SettingsIcon />} 
            label="Основные настройки" 
            iconPosition="start"
          />
          <Tab 
            icon={<ChannelsIcon />} 
            label={`Каналы (${botChannels.length})`}
            iconPosition="start"
          />
          <Tab 
            icon={<CategoriesIcon />} 
            label={`Категории (${botCategories.length})`}
            iconPosition="start"
          />
          <Tab 
            icon={<AIIcon />} 
            label="AI настройки"
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Основные настройки */}
      <TabPanel value={activeTab} index={0}>
        <BotGeneralSettings 
          bot={bot}
          onBotUpdate={onBotUpdate}
        />
      </TabPanel>

      {/* Каналы с bulk операциями */}
      <TabPanel value={activeTab} index={1}>
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ChannelsIcon />
          Управление каналами
          <Typography variant="body2" color="textSecondary">
            ({botChannels.length} каналов добавлено)
          </Typography>
        </Typography>
        
        <BotChannelsManager
          botId={bot.id}
          botChannels={botChannels}
          onChannelsChange={handleChannelsChange}
        />
      </TabPanel>

      {/* Категории с bulk операциями */}
      <TabPanel value={activeTab} index={2}>
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CategoriesIcon />
          Управление категориями
          <Typography variant="body2" color="textSecondary">
            ({botCategories.length} категорий добавлено)
          </Typography>
        </Typography>
        
        <BotCategoriesManager
          botId={bot.id}
          botCategories={botCategories}
          onCategoriesChange={handleCategoriesChange}
          onPriorityChange={handlePriorityChange}
        />
      </TabPanel>

      {/* AI настройки */}
      <TabPanel value={activeTab} index={3}>
        <BotAISettings 
          bot={bot}
          onBotUpdate={onBotUpdate}
        />
      </TabPanel>
    </Paper>
  );
};

export default BotConfigurationTabs; 