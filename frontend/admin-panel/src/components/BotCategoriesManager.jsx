import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Checkbox,
  TextField,
  Chip,
  Card,
  CardContent,
  Grid,
  Alert,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider
} from '@mui/material';
import {
  Add as AddIcon,
  Remove as RemoveIcon,
  Search as SearchIcon,
  FileDownload as ExportIcon,
  Sync as SyncIcon,
  Close as CloseIcon
} from '@mui/icons-material';

// Убираем шаблоны категорий (пока не нужны)
// const CATEGORY_TEMPLATES = { ... }

const BotCategoriesManager = ({ botId, botCategories, onCategoriesChange, onPriorityChange }) => {
  const [availableCategories, setAvailableCategories] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  // Загрузка доступных категорий
  useEffect(() => {
    loadAvailableCategories();
  }, [botId, botCategories]);

  const loadAvailableCategories = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/categories');
      if (!response.ok) throw new Error('Ошибка загрузки категорий');
      
      const categories = await response.json();
      // console.log('🔍 Загруженные категории:', categories); // Отладочный лог
      
      // Применяем ту же трансформацию, что и в CategoriesPage.jsx
      const transformedCategories = categories.map(category => ({
        ...category,
        name: category.category_name || category.name || ''
      }));
      
      // Фильтруем категории, которые еще не добавлены к боту
      const botCategoryIds = (botCategories || []).map(cat => cat.id);
      const available = transformedCategories.filter(cat => !botCategoryIds.includes(cat.id));
      
      // console.log('🔍 Трансформированные категории:', transformedCategories); // Отладочный лог
      // console.log('🔍 Доступные категории после фильтрации:', available); // Отладочный лог
      // console.log('🔍 Категории бота:', botCategories); // Отладочный лог
      
      setAvailableCategories(available);
      setError('');
    } catch (error) {
      console.error('Ошибка загрузки категорий:', error);
      setError('Ошибка загрузки категорий: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Фильтрация категорий по поиску
  const filteredCategories = availableCategories.filter(category =>
    (category.category_name || category.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (category.description || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Обработка выбора категорий
  const handleCategorySelect = (categoryId, selected) => {
    if (selected) {
      setSelectedCategories([...selectedCategories, categoryId]);
    } else {
      setSelectedCategories(selectedCategories.filter(id => id !== categoryId));
    }
  };

  // Выбрать все отфильтрованные категории
  const handleSelectAll = () => {
    const allIds = filteredCategories.map(cat => cat.id);
    setSelectedCategories(allIds);
  };

  // Очистить выбор
  const handleClearSelection = () => {
    setSelectedCategories([]);
  };

  // Bulk добавление выбранных категорий
  const handleBulkAdd = async () => {
    if (selectedCategories.length === 0) return;

    setLoading(true);
    try {
      // Генерируем автоматические приоритеты
      const priorities = selectedCategories.map((_, index) => 
        (botCategories || []).length + index + 1
      );

      // Используем реальный API для добавления категорий к боту
      const response = await fetch(`http://localhost:8000/api/public-bots/${botId}/categories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          category_ids: selectedCategories,
          priorities: priorities
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка добавления категорий');
      }

      // Получаем обновленный список категорий бота с реальными приоритетами
      const botCategoriesResponse = await fetch(`http://localhost:8000/api/public-bots/${botId}/categories`);
      if (botCategoriesResponse.ok) {
        const updatedBotCategories = await botCategoriesResponse.json();
        console.log(`🔄 Категории после добавления:`, updatedBotCategories);
        onCategoriesChange(updatedBotCategories);
      }
      
      // Очищаем выбор
      setSelectedCategories([]);
      setError('');
      
    } catch (error) {
      console.error('Ошибка добавления категорий:', error);
      setError('Ошибка добавления категорий: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Удаление категории из бота
  const handleRemoveCategory = async (categoryId) => {
    try {
      // Используем реальный API для удаления категории из бота
      const response = await fetch(`http://localhost:8000/api/public-bots/${botId}/categories/${categoryId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка удаления категории');
      }

      // Получаем обновленный список категорий бота с реальными приоритетами
      const botCategoriesResponse = await fetch(`http://localhost:8000/api/public-bots/${botId}/categories`);
      if (botCategoriesResponse.ok) {
        const updatedBotCategories = await botCategoriesResponse.json();
        console.log(`🔄 Категории после удаления:`, updatedBotCategories);
        onCategoriesChange(updatedBotCategories);
      }
      
      setError('');
      
    } catch (error) {
      console.error('Ошибка удаления категории:', error);
      setError('Ошибка удаления категории: ' + error.message);
    }
  };

  // Обработка изменения приоритета через слайдер
  const handlePrioritySliderChange = (categoryId, newPriority) => {
    console.log(`🎚️ Изменение приоритета: категория ${categoryId}, приоритет ${newPriority}`);
    
    // Мгновенно обновляем UI
    const updatedCategories = (botCategories || []).map(cat => 
      cat.id === categoryId ? { 
        ...cat, 
        weight: newPriority,
        priority: newPriority
      } : cat
    );
    onCategoriesChange(updatedCategories);

    // Уведомляем родительский компонент об изменении приоритета
    if (onPriorityChange) {
      onPriorityChange(categoryId, newPriority);
    }
  };

  // Экспорт категорий в CSV
  const handleExport = () => {
    const csvContent = [
      'ID,Название,Описание,Приоритет',
      ...(botCategories || []).map(cat => 
        `${cat.id},"${cat.name}","${cat.description || ''}",${cat.priority || 0}`
      )
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bot_${botId}_categories.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}



      {/* Header с поиском и bulk действиями */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, flexWrap: 'wrap', gap: 2 }}>
        <TextField
          placeholder="Поиск категорий..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
          }}
          sx={{ minWidth: 300 }}
        />
        
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button
            variant="outlined"
            startIcon={<ExportIcon />}
            onClick={handleExport}
            disabled={(botCategories || []).length === 0}
          >
            Экспорт
          </Button>
          <Button
            variant="outlined"
            startIcon={<SyncIcon />}
            onClick={loadAvailableCategories}
            disabled={loading}
          >
            Обновить
          </Button>
        </Box>
      </Box>

      {/* Статистика */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="primary" component="div">
                {(botCategories || []).length}
              </Typography>
              <Typography variant="body2" color="text.secondary" component="div">
                Добавленные категории
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="secondary" component="div">
                {availableCategories.length}
              </Typography>
              <Typography variant="body2" color="text.secondary" component="div">
                Доступные категории
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="info.main" component="div">
                {selectedCategories.length}
              </Typography>
              <Typography variant="body2" color="text.secondary" component="div">
                Выбрано
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary" component="div">
                {filteredCategories.length}
              </Typography>
              <Typography variant="body2" color="text.secondary" component="div">
                По фильтру
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Добавленные категории с управлением приоритетами */}
      {(botCategories || []).length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Добавленные категории ({(botCategories || []).length})
          </Typography>
          <Grid container spacing={2}>
            {(botCategories || [])
              // .sort((a, b) => (a.priority || 0) - (b.priority || 0)) // Убираем сортировку
              .map(category => {
                // Применяем ту же трансформацию для отображения
                const displayCategory = {
                  ...category,
                  name: category.category_name || category.name || ''
                };
                
                return (
              <Grid item xs={12} sm={6} md={4} key={category.id}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                        {displayCategory.name || `[ID: ${category.id}]`}
                      </Typography>
                      <IconButton 
                        size="small" 
                        onClick={() => handleRemoveCategory(category.id)}
                        sx={{ color: 'error.main' }}
                      >
                        <CloseIcon />
                      </IconButton>
                    </Box>
                    
                    {/* Убираем описание категории, оставляем только название */}
                    {/* {category.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {category.description}
                      </Typography>
                    )} */}
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Приоритет: {category.weight || category.priority || 1}
                      </Typography>
                    </Box>
                    
                    <Slider
                      value={category.weight || category.priority || 1}
                      onChange={(e, value) => handlePrioritySliderChange(category.id, value)}
                      min={1}
                      max={10}
                      step={1}
                      marks
                      valueLabelDisplay="auto"
                      size="small"
                    />
                  </CardContent>
                </Card>
              </Grid>
                );
              })}
          </Grid>
        </Box>
      )}

      <Divider sx={{ my: 2 }} />

      {/* Bulk selection controls */}
      {availableCategories.length > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button size="small" onClick={handleSelectAll}>
              Выбрать все ({filteredCategories.length})
            </Button>
            <Button size="small" onClick={handleClearSelection}>
              Очистить выбор
            </Button>
          </Box>
          
          {selectedCategories.length > 0 && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleBulkAdd}
              disabled={loading}
            >
              Добавить выбранные ({selectedCategories.length})
            </Button>
          )}
        </Box>
      )}

      {/* Список доступных категорий */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : (
        <List>
          {filteredCategories.map(category => (
            <ListItem key={category.id} divider>
              <ListItemIcon>
                <Checkbox
                  checked={selectedCategories.includes(category.id)}
                  onChange={(e) => handleCategorySelect(category.id, e.target.checked)}
                />
              </ListItemIcon>
              <Box sx={{ flex: 1, ml: 2 }}>
                <Typography variant="body1" component="div">
                  {category.name || `[ID: ${category.id}]`}
                </Typography>
                {category.description && (
                  <Typography variant="body2" color="text.secondary" component="div">
                    {category.description}
                  </Typography>
                )}
              </Box>
              <ListItemSecondaryAction>
                <IconButton
                  edge="end"
                  onClick={() => handleCategorySelect(category.id, !selectedCategories.includes(category.id))}
                >
                  {selectedCategories.includes(category.id) ? <RemoveIcon /> : <AddIcon />}
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      )}

      {filteredCategories.length === 0 && !loading && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body1" color="text.secondary">
            {searchTerm ? 'Категории не найдены по запросу' : 'Все доступные категории уже добавлены'}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default BotCategoriesManager; 