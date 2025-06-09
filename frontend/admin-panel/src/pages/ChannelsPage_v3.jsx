import React, { useState, useMemo, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  Avatar,
  DialogContentText,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  InputAdornment,
  Grid,
  Alert,
  CircularProgress,
  Card,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Telegram as TelegramIcon,
  Warning as WarningIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Category as CategoryIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
  SmartToy as SmartToyIcon,
} from '@mui/icons-material';
import apiService from '../services/api';
import ChannelCategoriesDialog from '../components/ChannelCategoriesDialog';

export default function ChannelsPage() {
  const [channels, setChannels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [open, setOpen] = useState(false);
  const [editingChannel, setEditingChannel] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [channelToDelete, setChannelToDelete] = useState(null);
  const [categoriesDialogOpen, setCategoriesDialogOpen] = useState(false);
  const [channelForCategories, setChannelForCategories] = useState(null);

  // Search and filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all'); // 'all', 'active', 'inactive'

  // Form validation states
  const [formData, setFormData] = useState({
    title: '',
    username: '',
    description: '',
    telegram_id: '',
    is_active: true
  });
  const [formErrors, setFormErrors] = useState({});
  const [touched, setTouched] = useState({});

  // Channel validation states
  const [channelInput, setChannelInput] = useState('');
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [showManualForm, setShowManualForm] = useState(false);

  useEffect(() => {
    loadChannels();
  }, []);

  const loadChannels = async () => {
    try {
      setLoading(true);
      const data = await apiService.getChannels();
      setChannels(data);
      setError(null);
    } catch (err) {
      setError('Не удалось загрузить каналы: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Validation rules
  const validateField = (name, value) => {
    switch (name) {
      case 'title':
        if (!value || value.trim().length < 2) {
          return 'Название канала должно содержать минимум 2 символа';
        }
        if (value.trim().length > 100) {
          return 'Название канала не должно превышать 100 символов';
        }
        // Check for duplicate names (excluding current editing channel)
        const isDuplicateName = channels.some(channel => 
          channel.title.toLowerCase() === value.trim().toLowerCase() && 
          channel.id !== editingChannel?.id
        );
        if (isDuplicateName) {
          return 'Канал с таким названием уже существует';
        }
        return '';
      
      case 'username':
        if (!value || value.trim().length === 0) {
          return 'Username обязателен';
        }
        if (!value.trim().startsWith('@')) {
          return 'Username должен начинаться с @';
        }
        if (value.trim().length < 2) {
          return 'Username должен содержать минимум 2 символа (включая @)';
        }
        if (value.trim().length > 33) {
          return 'Username не должен превышать 33 символа';
        }
        // Check for valid username format (only letters, numbers, underscores)
        const usernamePattern = /^@[a-zA-Z0-9_]+$/;
        if (!usernamePattern.test(value.trim())) {
          return 'Username может содержать только буквы, цифры и подчеркивания';
        }
        // Check for duplicate usernames (excluding current editing channel)
        const isDuplicateUsername = channels.some(channel => 
          channel.username.toLowerCase() === value.trim().toLowerCase() && 
          channel.id !== editingChannel?.id
        );
        if (isDuplicateUsername) {
          return 'Канал с таким username уже существует';
        }
        return '';
      
      case 'description':
        if (value && value.trim().length > 500) {
          return 'Описание не должно превышать 500 символов';
        }
        return '';
      
      case 'telegram_id':
        if (!value) {
          return 'Telegram ID обязателен';
        }
        const telegramId = parseInt(value);
        if (isNaN(telegramId)) {
          return 'Telegram ID должен быть числом';
        }
        // Check for duplicate telegram_id (excluding current editing channel)
        const isDuplicateTelegramId = channels.some(channel => 
          channel.telegram_id === telegramId && 
          channel.id !== editingChannel?.id
        );
        if (isDuplicateTelegramId) {
          return 'Канал с таким Telegram ID уже существует';
        }
        return '';
      
      default:
        return '';
    }
  };

  const validateForm = () => {
    const errors = {};
    Object.keys(formData).forEach(field => {
      if (field !== 'is_active') { // Skip validation for switch
        const error = validateField(field, formData[field]);
        if (error) {
          errors[field] = error;
        }
      }
    });
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleFieldChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Real-time validation
    if (touched[field]) {
      const error = validateField(field, value);
      setFormErrors(prev => ({ ...prev, [field]: error }));
    }
  };

  const handleFieldBlur = (field) => {
    setTouched(prev => ({ ...prev, [field]: true }));
    const error = validateField(field, formData[field]);
    setFormErrors(prev => ({ ...prev, [field]: error }));
  };

  // Channel validation functions
  const validateChannel = async () => {
    if (!channelInput.trim()) {
      setValidationResult({ error: 'Введите идентификатор канала' });
      return;
    }

    setValidating(true);
    setValidationResult(null);

    try {
      const response = await apiService.request('/channels/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel_input: channelInput.trim() })
      });

      if (response.success) {
        setValidationResult({
          success: true,
          data: response.data,
          message: 'Канал найден и успешно проверен!'
        });
      } else {
        setValidationResult({
          error: response.error || 'Не удалось проверить канал'
        });
      }
    } catch (error) {
      setValidationResult({
        error: 'Ошибка сети: ' + error.message
      });
    } finally {
      setValidating(false);
    }
  };

  const applyValidationResult = () => {
    if (validationResult?.success && validationResult.data) {
      const data = validationResult.data;
      setFormData({
        title: data.title || '',
        username: data.username || '',
        description: data.description || '',
        telegram_id: data.telegram_id?.toString() || '',
        is_active: true
      });
      setFormErrors({});
      setTouched({});
      setShowManualForm(true);
      setValidationResult(null);
      setChannelInput('');
    }
  };

  const resetValidation = () => {
    setChannelInput('');
    setValidationResult(null);
    setShowManualForm(false);
  };

  const handleClickOpen = () => {
    setEditingChannel(null);
    setFormData({
      title: '',
      username: '',
      description: '',
      telegram_id: '',
      is_active: true
    });
    setFormErrors({});
    setTouched({});
    setChannelInput('');
    setValidationResult(null);
    setShowManualForm(false);
    setOpen(true);
  };

  const handleEdit = (channel) => {
    setEditingChannel(channel);
    setFormData({
      title: channel.title,
      username: channel.username,
      description: channel.description || '',
      telegram_id: channel.telegram_id.toString(),
      is_active: channel.is_active
    });
    setFormErrors({});
    setTouched({});
    setChannelInput('');
    setValidationResult(null);
    setShowManualForm(true);
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setEditingChannel(null);
    setFormData({
      title: '',
      username: '',
      description: '',
      telegram_id: '',
      is_active: true
    });
    setFormErrors({});
    setTouched({});
    setChannelInput('');
    setValidationResult(null);
    setShowManualForm(false);
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    setSaving(true);
    try {
      const channelData = {
        ...formData,
        telegram_id: parseInt(formData.telegram_id)
      };

      if (editingChannel) {
        await apiService.updateChannel(editingChannel.id, channelData);
      } else {
        await apiService.createChannel(channelData);
      }
      
      await loadChannels();
      handleClose();
    } catch (err) {
      setError('Не удалось сохранить канал: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteClick = (channel) => {
    setChannelToDelete(channel);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (channelToDelete) {
      try {
        await apiService.deleteChannel(channelToDelete.id);
        await loadChannels();
        setDeleteDialogOpen(false);
        setChannelToDelete(null);
      } catch (err) {
        setError('Не удалось удалить канал: ' + err.message);
      }
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setChannelToDelete(null);
  };

  const handleManageCategories = (channel) => {
    setChannelForCategories(channel);
    setCategoriesDialogOpen(true);
  };

  const handleCategoriesDialogClose = () => {
    setCategoriesDialogOpen(false);
    setChannelForCategories(null);
  };

  const handleCategoriesUpdate = () => {
    loadChannels();
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setStatusFilter('all');
  };

  // Filtered channels
  const filteredChannels = useMemo(() => {
    return channels.filter(channel => {
      const matchesSearch = !searchQuery || 
        channel.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        channel.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (channel.description && channel.description.toLowerCase().includes(searchQuery.toLowerCase()));
      
      const matchesStatus = statusFilter === 'all' || 
        (statusFilter === 'active' && channel.is_active) ||
        (statusFilter === 'inactive' && !channel.is_active);
      
      return matchesSearch && matchesStatus;
    });
  }, [channels, searchQuery, statusFilter]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Каналы
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleClickOpen}
        >
          Добавить канал
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Search and Filter Controls */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              size="small"
              placeholder="Поиск каналов..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} sm={4} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Статус</InputLabel>
              <Select
                value={statusFilter}
                label="Статус"
                onChange={(e) => setStatusFilter(e.target.value)}
                startAdornment={<FilterIcon sx={{ mr: 1, color: 'action.active' }} />}
              >
                <MenuItem value="all">Все</MenuItem>
                <MenuItem value="active">Активные</MenuItem>
                <MenuItem value="inactive">Неактивные</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={2} md={2}>
            <Button
              variant="outlined"
              onClick={handleClearFilters}
              disabled={!searchQuery && statusFilter === 'all'}
            >
              Сбросить
            </Button>
          </Grid>
          <Grid item xs={12} sm={12} md={3}>
            <Typography variant="body2" color="text.secondary">
              Найдено: {filteredChannels.length} из {channels.length} каналов
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Канал</TableCell>
              <TableCell>Username</TableCell>
              <TableCell>Описание</TableCell>
              <TableCell>Telegram ID</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell>Категории</TableCell>
              <TableCell align="right">Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredChannels.map((channel) => (
              <TableRow key={channel.id}>
                <TableCell>
                  <Box display="flex" alignItems="center">
                    <Avatar sx={{ width: 32, height: 32, mr: 2 }}>
                      <TelegramIcon />
                    </Avatar>
                    <Typography variant="body2" fontWeight="medium">
                      {channel.title}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {channel.username}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography 
                    variant="body2" 
                    color="text.secondary"
                    sx={{
                      maxWidth: 200,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {channel.description || 'Без описания'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" fontFamily="monospace">
                    {channel.telegram_id}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={channel.is_active ? 'Активен' : 'Неактивен'}
                    color={channel.is_active ? 'success' : 'default'}
                    size="small"
                    icon={channel.is_active ? <CheckCircleIcon /> : <WarningIcon />}
                  />
                </TableCell>
                <TableCell>
                  <Button
                    size="small"
                    startIcon={<CategoryIcon />}
                    onClick={() => handleManageCategories(channel)}
                    variant="outlined"
                  >
                    Категории
                  </Button>
                </TableCell>
                <TableCell align="right">
                  <IconButton
                    size="small"
                    onClick={() => handleEdit(channel)}
                    color="primary"
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteClick(channel)}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {filteredChannels.length === 0 && (
        <Paper sx={{ p: 4, textAlign: 'center', mt: 3 }}>
          <InfoIcon color="action" sx={{ fontSize: 48, mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {channels.length === 0 ? 'Каналы не найдены' : 'Нет каналов, соответствующих фильтрам'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {channels.length === 0 
              ? 'Добавьте первый канал, нажав кнопку "Добавить канал"'
              : 'Попробуйте изменить критерии поиска или сбросить фильтры'
            }
          </Typography>
        </Paper>
      )}

      {/* Add/Edit Dialog */}
      <Dialog 
        open={open} 
        onClose={handleClose}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingChannel ? 'Редактировать канал' : 'Добавить канал'}
        </DialogTitle>
        <DialogContent>
          {!editingChannel && !showManualForm && (
            <Card sx={{ p: 3, mb: 3, bgcolor: 'background.default' }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SmartToyIcon color="primary" />
                Умная проверка канала
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Введите канал в любом формате:
              </Typography>
              <Typography variant="body2" color="text.secondary" component="ul" sx={{ mb: 2, pl: 2 }}>
                <li>@username (например: @breakingmash)</li>
                <li>username (например: breakingmash)</li>  
                <li>https://t.me/username</li>
                <li>Telegram ID (например: -1001234567890)</li>
              </Typography>
              
              <TextField
                fullWidth
                label="Идентификатор канала"
                value={channelInput}
                onChange={(e) => setChannelInput(e.target.value)}
                placeholder="@breakingmash, breakingmash, https://t.me/breakingmash или Telegram ID"
                margin="normal"
                disabled={validating}
              />
              
              <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                <Button
                  variant="contained"
                  onClick={validateChannel}
                  disabled={validating || !channelInput.trim()}
                  startIcon={validating ? <CircularProgress size={20} /> : <SmartToyIcon />}
                >
                  {validating ? 'Проверяю...' : 'Проверить канал'}
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => setShowManualForm(true)}
                >
                  Заполнить форму вручную
                </Button>
              </Box>

              {validationResult && (
                <Box sx={{ mt: 2 }}>
                  {validationResult.success ? (
                    <Alert 
                      severity="success" 
                      action={
                        <Button color="inherit" size="small" onClick={applyValidationResult}>
                          Использовать
                        </Button>
                      }
                    >
                      {validationResult.message}
                      <br />
                      <strong>Название:</strong> {validationResult.data.title}<br />
                      <strong>Username:</strong> {validationResult.data.username}<br />
                      {validationResult.data.description && (
                        <>
                          <strong>Описание:</strong> {validationResult.data.description.slice(0, 100)}
                          {validationResult.data.description.length > 100 && '...'}<br />
                        </>
                      )}
                      <strong>Telegram ID:</strong> {validationResult.data.telegram_id}<br />
                      <strong>Подписчики:</strong> {validationResult.data.subscribers}
                    </Alert>
                  ) : (
                    <Alert severity="error">
                      {validationResult.error}
                    </Alert>
                  )}
                </Box>
              )}
            </Card>
          )}

          {(showManualForm || editingChannel) && (
            <>
              <TextField
                autoFocus
                margin="dense"
                label="Название канала"
                fullWidth
                variant="outlined"
                value={formData.title}
                onChange={(e) => handleFieldChange('title', e.target.value)}
                onBlur={() => handleFieldBlur('title')}
                error={!!formErrors.title}
                helperText={formErrors.title}
                sx={{ mb: 2 }}
              />
              <TextField
                margin="dense"
                label="Username"
                fullWidth
                variant="outlined"
                value={formData.username}
                onChange={(e) => handleFieldChange('username', e.target.value)}
                onBlur={() => handleFieldBlur('username')}
                error={!!formErrors.username}
                helperText={formErrors.username}
                placeholder="@example"
                sx={{ mb: 2 }}
              />
              <TextField
                margin="dense"
                label="Описание"
                fullWidth
                variant="outlined"
                multiline
                rows={3}
                value={formData.description}
                onChange={(e) => handleFieldChange('description', e.target.value)}
                onBlur={() => handleFieldBlur('description')}
                error={!!formErrors.description}
                helperText={formErrors.description}
                sx={{ mb: 2 }}
              />
              <TextField
                margin="dense"
                label="Telegram ID"
                fullWidth
                variant="outlined"
                value={formData.telegram_id}
                onChange={(e) => handleFieldChange('telegram_id', e.target.value)}
                onBlur={() => handleFieldBlur('telegram_id')}
                error={!!formErrors.telegram_id}
                helperText={formErrors.telegram_id}
                placeholder="-1001234567890"
                sx={{ mb: 2 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active}
                    onChange={(e) => handleFieldChange('is_active', e.target.checked)}
                  />
                }
                label="Активен"
              />
              
              {!editingChannel && (
                <Box sx={{ mt: 2 }}>
                  <Button
                    variant="outlined"
                    onClick={resetValidation}
                    startIcon={<SmartToyIcon />}
                  >
                    Вернуться к умной проверке
                  </Button>
                </Box>
              )}
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>
            Отмена
          </Button>
          <Button 
            onClick={handleSave} 
            variant="contained"
            disabled={saving || (!showManualForm && !editingChannel)}
          >
            {saving ? 'Сохранение...' : (editingChannel ? 'Обновить' : 'Добавить')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
      >
        <DialogTitle>Подтвердить удаление</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Вы действительно хотите удалить канал "{channelToDelete?.title}"?
            Это действие нельзя отменить.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel}>
            Отмена
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Удалить
          </Button>
        </DialogActions>
      </Dialog>

      {/* Channel Categories Dialog */}
      <ChannelCategoriesDialog
        open={categoriesDialogOpen}
        onClose={handleCategoriesDialogClose}
        channel={channelForCategories}
        onUpdate={handleCategoriesUpdate}
      />
    </Box>
  );
} 