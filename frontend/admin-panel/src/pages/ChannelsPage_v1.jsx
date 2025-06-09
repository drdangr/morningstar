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
      setError('Failed to load channels: ' + err.message);
    } finally {
      setLoading(false);
    }
  };



  // Validation rules
  const validateField = (name, value) => {
    switch (name) {
      case 'title':
        if (!value || value.trim().length < 2) {
          return 'Channel name must be at least 2 characters long';
        }
        if (value.trim().length > 50) {
          return 'Channel name must be less than 50 characters';
        }
        // Check for duplicate names (excluding current editing channel)
        const isDuplicateName = channels.some(channel => 
          channel.title.toLowerCase() === value.trim().toLowerCase() && 
          channel.id !== editingChannel?.id
        );
        if (isDuplicateName) {
          return 'A channel with this name already exists';
        }
        return '';
      
      case 'username':
        if (!value || value.trim().length === 0) {
          return 'Username is required';
        }
        if (!value.trim().startsWith('@')) {
          return 'Username must start with @';
        }
        if (value.trim().length < 2) {
          return 'Username must be at least 2 characters long (including @)';
        }
        if (value.trim().length > 33) {
          return 'Username must be less than 33 characters';
        }
        // Check for valid username format (only letters, numbers, underscores)
        const usernamePattern = /^@[a-zA-Z0-9_]+$/;
        if (!usernamePattern.test(value.trim())) {
          return 'Username can only contain letters, numbers and underscores';
        }
        // Check for duplicate usernames (excluding current editing channel)
        const isDuplicateUsername = channels.some(channel => 
          channel.username.toLowerCase() === value.trim().toLowerCase() && 
          channel.id !== editingChannel?.id
        );
        if (isDuplicateUsername) {
          return 'A channel with this username already exists';
        }
        return '';
      
      case 'description':
        if (value && value.trim().length > 500) {
          return 'Description must be less than 500 characters';
        }
        return '';
      
      case 'telegram_id':
        if (!value) {
          return 'Telegram ID is required';
        }
        const telegramId = parseInt(value);
        if (isNaN(telegramId)) {
          return 'Telegram ID must be a number';
        }
        // Check for duplicate telegram_id (excluding current editing channel)
        const isDuplicateTelegramId = channels.some(channel => 
          channel.telegram_id === telegramId && 
          channel.id !== editingChannel?.id
        );
        if (isDuplicateTelegramId) {
          return 'A channel with this Telegram ID already exists';
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

  // Filtered channels based on search and filters
  const filteredChannels = useMemo(() => {
    return channels.filter(channel => {
      // Search filter
      const matchesSearch = searchQuery === '' || 
        channel.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (channel.username && channel.username.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (channel.description && channel.description.toLowerCase().includes(searchQuery.toLowerCase()));
      
      // Status filter
      const matchesStatus = statusFilter === 'all' || 
        (statusFilter === 'active' && channel.is_active) ||
        (statusFilter === 'inactive' && !channel.is_active);
      
      return matchesSearch && matchesStatus;
    });
  }, [channels, searchQuery, statusFilter]);

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
    setOpen(true);
  };

  const handleEdit = (channel) => {
    setEditingChannel(channel);
    setFormData({
      title: channel.title,
      username: channel.username || '',
      description: channel.description || '',
      telegram_id: channel.telegram_id.toString(),
      is_active: channel.is_active
    });
    setFormErrors({});
    setTouched({});
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
  };

  const handleSave = async () => {
    // Mark all fields as touched for validation display
    setTouched({
      title: true,
      username: true,
      description: true,
      telegram_id: true
    });

    if (!isFormValid) {
      return; // Don't save if validation fails
    }

    setSaving(true);
    setError('');

    try {
      const channelData = {
        title: formData.title.trim(),
        username: formData.username.trim() || null,
        description: formData.description.trim() || null,
        telegram_id: parseInt(formData.telegram_id),
        is_active: formData.is_active
      };

      if (editingChannel) {
        // Update existing channel
        await apiService.updateChannel(editingChannel.id, channelData);
      } else {
        // Create new channel
        await apiService.createChannel(channelData);
      }

      await loadChannels();
      handleClose();
    } catch (err) {
      console.error('Error saving channel:', err);
      setError(err.message || 'Error saving channel');
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
        console.error('Error deleting channel:', err);
        setError(err.message || 'Error deleting channel');
        setDeleteDialogOpen(false);
        setChannelToDelete(null);
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
    // Можно обновить таблицу если нужно показывать категории
    loadChannels();
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setStatusFilter('all');
  };

  const isFormValid = Object.keys(formErrors).every(key => !formErrors[key]) && 
                     formData.title.trim() && 
                     formData.telegram_id;

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <div>
          <Typography variant="h4" gutterBottom>
            Channels Management
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Управление Telegram каналами для мониторинга
          </Typography>
        </div>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleClickOpen}
        >
          Add Channel
        </Button>
      </Box>

      {/* Search and Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={5}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Search channels by name, username, description, or topics..."
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
          <Grid item xs={12} md={2}>
            <FormControl fullWidth variant="outlined">
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                label="Status"
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="inactive">Inactive</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={4}>
            <Button 
              variant="outlined" 
              onClick={handleClearFilters}
              fullWidth
              startIcon={<FilterIcon />}
            >
              Clear Filters
            </Button>
          </Grid>
        </Grid>
        
        {/* Results info */}
        <Box mt={2}>
          <Typography variant="body2" color="textSecondary">
            Showing {filteredChannels.length} of {channels.length} channels
            {searchQuery && ` (filtered by "${searchQuery}")`}
            {statusFilter !== 'all' && ` (${statusFilter} only)`}
          </Typography>
        </Box>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Channel</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Topics</TableCell>
              <TableCell>Telegram ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredChannels.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                  <Typography variant="body1" color="textSecondary">
                    {searchQuery || statusFilter !== 'all'
                      ? 'No channels match your search criteria' 
                      : 'No channels found'
                    }
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredChannels.map((channel) => (
                <TableRow key={channel.id}>
                  <TableCell component="th" scope="row">
                    <Box display="flex" alignItems="center" gap={2}>
                      <Avatar sx={{ bgcolor: 'primary.main' }}>
                        <TelegramIcon />
                      </Avatar>
                      <div>
                        <Typography variant="subtitle2">
                          {channel.title}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          {channel.username || 'No username'}
                        </Typography>
                      </div>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {channel.description || 'No description'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={1} flexWrap="wrap">
                      {channel.categories && channel.categories.length > 0 ? (
                        channel.categories.map((category) => (
                          <Chip
                            key={category.id}
                            label={`${category.emoji} ${category.name}`}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                        ))
                      ) : (
                        <Typography variant="body2" color="textSecondary">
                          No topics
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {channel.telegram_id}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={channel.is_active ? 'Active' : 'Inactive'}
                      color={channel.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton 
                      onClick={() => handleManageCategories(channel)} 
                      size="small"
                      title="Manage Topics"
                    >
                      <CategoryIcon />
                    </IconButton>
                    <IconButton onClick={() => handleEdit(channel)} size="small">
                      <EditIcon />
                    </IconButton>
                    <IconButton 
                      onClick={() => handleDeleteClick(channel)} 
                      size="small"
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add/Edit Dialog */}
      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingChannel ? 'Edit Channel' : 'Add New Channel'}
        </DialogTitle>
        <DialogContent>
          {/* Form validation summary */}
          {Object.keys(formErrors).some(key => formErrors[key] && touched[key]) && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Please fix the following errors before saving.
            </Alert>
          )}

          <TextField
            autoFocus
            margin="dense"
            label="Channel Title"
            fullWidth
            variant="outlined"
            value={formData.title}
            onChange={(e) => handleFieldChange('title', e.target.value)}
            onBlur={() => handleFieldBlur('title')}
            error={touched.title && !!formErrors.title}
            helperText={touched.title && formErrors.title}
            sx={{ mb: 2 }}
            required
          />
          <TextField
            margin="dense"
            label="Username"
            fullWidth
            variant="outlined"
            value={formData.username}
            onChange={(e) => handleFieldChange('username', e.target.value)}
            onBlur={() => handleFieldBlur('username')}
            error={touched.username && !!formErrors.username}
            helperText={touched.username && formErrors.username ? formErrors.username : 'Telegram username with @ (e.g., @techcrunch)'}
            sx={{ mb: 2 }}
            placeholder="@username"
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={formData.description}
            onChange={(e) => handleFieldChange('description', e.target.value)}
            onBlur={() => handleFieldBlur('description')}
            error={touched.description && !!formErrors.description}
            helperText={touched.description && formErrors.description ? formErrors.description : 'Describe what content this channel provides'}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Telegram ID"
            fullWidth
            variant="outlined"
            type="number"
            value={formData.telegram_id}
            onChange={(e) => handleFieldChange('telegram_id', e.target.value)}
            onBlur={() => handleFieldBlur('telegram_id')}
            error={touched.telegram_id && !!formErrors.telegram_id}
            helperText={touched.telegram_id && formErrors.telegram_id ? formErrors.telegram_id : 'Unique Telegram channel ID (numeric)'}
            sx={{ mb: 2 }}
            required
          />
          <FormControlLabel
            control={
              <Switch 
                checked={formData.is_active} 
                onChange={(e) => handleFieldChange('is_active', e.target.checked)}
              />
            }
            label="Active"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button 
            onClick={handleSave} 
            variant="contained"
            disabled={!isFormValid}
          >
            {editingChannel ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningIcon color="warning" />
          Confirm Deletion
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the channel <strong>"{channelToDelete?.title}"</strong> ({channelToDelete?.username || 'No username'})?
          </DialogContentText>
          <DialogContentText sx={{ mt: 2, color: 'warning.main' }}>
            <strong>Warning:</strong> This action cannot be undone. All posts from this channel will no longer be monitored.
          </DialogContentText>
          {channelToDelete && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="body2" color="textSecondary">
                Channel details:
              </Typography>
              <Typography variant="body2">
                • Telegram ID: {channelToDelete.telegram_id}
              </Typography>
              <Typography variant="body2">
                • Description: {channelToDelete.description || 'No description'}
              </Typography>
              <Typography variant="body2">
                • Status: {channelToDelete.is_active ? 'Active' : 'Inactive'}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel}>
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteConfirm} 
            variant="contained" 
            color="error"
            startIcon={<DeleteIcon />}
          >
            Delete Channel
          </Button>
        </DialogActions>
      </Dialog>

      {/* Categories Management Dialog */}
      <ChannelCategoriesDialog
        open={categoriesDialogOpen}
        onClose={handleCategoriesDialogClose}
        channel={channelForCategories}
        onUpdate={handleCategoriesUpdate}
      />
    </Box>
  );
} 