import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Chip,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import apiService from '../services/api';

export default function ChannelCategoriesDialog({ 
  open, 
  onClose, 
  channel, 
  onUpdate 
}) {
  const [channelCategories, setChannelCategories] = useState([]);
  const [allCategories, setAllCategories] = useState([]);
  const [availableCategories, setAvailableCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedCategoryId, setSelectedCategoryId] = useState('');

  useEffect(() => {
    if (open && channel) {
      loadData();
    }
  }, [open, channel]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');

      // Загружаем категории канала и все доступные категории
      const [channelCats, allCats] = await Promise.all([
        apiService.get(`/channels/${channel.id}/categories`),
        apiService.getCategories()
      ]);

      setChannelCategories(channelCats);
      setAllCategories(allCats);

      // Фильтруем доступные категории (исключаем уже привязанные)
      const channelCategoryIds = channelCats.map(cat => cat.id);
      const available = allCats.filter(cat => !channelCategoryIds.includes(cat.id));
      setAvailableCategories(available);

    } catch (err) {
      console.error('Error loading categories:', err);
      setError('Failed to load categories: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddCategory = async () => {
    if (!selectedCategoryId) return;

    try {
      setLoading(true);
      setError('');

      await apiService.post(`/channels/${channel.id}/categories/${selectedCategoryId}`);
      
      // Обновляем данные
      await loadData();
      setSelectedCategoryId('');
      
      // Уведомляем родительский компонент об обновлении
      if (onUpdate) {
        onUpdate();
      }

    } catch (err) {
      console.error('Error adding category:', err);
      setError('Failed to add category: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveCategory = async (categoryId) => {
    try {
      setLoading(true);
      setError('');

      await apiService.delete(`/channels/${channel.id}/categories/${categoryId}`);
      
      // Обновляем данные
      await loadData();
      
      // Уведомляем родительский компонент об обновлении
      if (onUpdate) {
        onUpdate();
      }

    } catch (err) {
      console.error('Error removing category:', err);
      setError('Failed to remove category: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Управление категориями канала: {channel?.title}
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {/* Текущие категории канала */}
        <Box mb={3}>
          <Typography variant="h6" gutterBottom>
            Назначенные категории ({channelCategories.length})
          </Typography>
          
          {loading && channelCategories.length === 0 ? (
            <CircularProgress size={24} />
          ) : channelCategories.length === 0 ? (
            <Typography variant="body2" color="textSecondary">
              У этого канала пока нет назначенных категорий
            </Typography>
          ) : (
            <Box display="flex" gap={1} flexWrap="wrap">
              {channelCategories.map((category) => (
                <Chip
                  key={category.id}
                  label={`${category.emoji} ${category.name}`}
                  onDelete={() => handleRemoveCategory(category.id)}
                  deleteIcon={<CloseIcon />}
                  color="primary"
                  variant="filled"
                  disabled={loading}
                />
              ))}
            </Box>
          )}
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Добавление новой категории */}
        <Box>
          <Typography variant="h6" gutterBottom>
            Добавить категорию
          </Typography>
          
          <Box display="flex" gap={2} alignItems="center">
            <FormControl fullWidth variant="outlined" disabled={loading}>
              <InputLabel>Выберите категорию</InputLabel>
              <Select
                value={selectedCategoryId}
                onChange={(e) => setSelectedCategoryId(e.target.value)}
                label="Выберите категорию"
              >
                {availableCategories.length === 0 ? (
                  <MenuItem disabled>
                    Нет доступных категорий
                  </MenuItem>
                ) : (
                  availableCategories.map((category) => (
                    <MenuItem key={category.id} value={category.id}>
                      {category.emoji} {category.name}
                    </MenuItem>
                  ))
                )}
              </Select>
            </FormControl>
            
            <Button
              variant="contained"
              onClick={handleAddCategory}
              disabled={!selectedCategoryId || loading}
              startIcon={loading ? <CircularProgress size={20} /> : <AddIcon />}
            >
              Добавить
            </Button>
          </Box>

          {availableCategories.length === 0 && allCategories.length > 0 && (
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              Все доступные категории уже назначены этому каналу
            </Typography>
          )}
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Закрыть</Button>
      </DialogActions>
    </Dialog>
  );
} 