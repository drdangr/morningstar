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
  Warning as WarningIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import apiService from '../services/api';

const mockTopics = [
  { id: 1, name: 'Technology', description: 'Tech news and updates', keywords: ['tech', 'AI', 'software'], active: true },
  { id: 2, name: 'Crypto', description: 'Cryptocurrency and blockchain', keywords: ['bitcoin', 'ethereum', 'crypto'], active: true },
  { id: 3, name: 'Politics', description: 'Political news and events', keywords: ['politics', 'government', 'elections'], active: false },
];

export default function TopicsPage() {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [open, setOpen] = useState(false);
  const [editingTopic, setEditingTopic] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [topicToDelete, setTopicToDelete] = useState(null);
  
  // Search and filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all'); // 'all', 'active', 'inactive'

  // Form validation states
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    emoji: '📝',
    is_active: true,
    ai_prompt: '',
    sort_order: 0
  });
  const [formErrors, setFormErrors] = useState({});
  const [touched, setTouched] = useState({});

  useEffect(() => {
    loadTopics();
  }, []);

  const loadTopics = async () => {
    try {
      setLoading(true);
      const data = await apiService.getCategories();
      setTopics(data);
      setError(null);
    } catch (err) {
      setError('Failed to load topics: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Validation rules
  const validateField = (name, value) => {
    switch (name) {
      case 'name':
        if (!value || value.trim().length < 2) {
          return 'Topic name must be at least 2 characters long';
        }
        if (value.trim().length > 50) {
          return 'Topic name must be less than 50 characters';
        }
        // Check for duplicate names (excluding current editing topic)
        const isDuplicate = topics.some(topic => 
          topic.name.toLowerCase() === value.trim().toLowerCase() && 
          topic.id !== editingTopic?.id
        );
        if (isDuplicate) {
          return 'A topic with this name already exists';
        }
        return '';
      
      case 'description':
        if (value && value.trim().length > 500) {
          return 'Description must be less than 500 characters';
        }
        return '';
      
      case 'emoji':
        if (value && value.length > 10) {
          return 'Emoji must be less than 10 characters';
        }
        return '';
      
      case 'ai_prompt':
        if (value && value.trim().length > 1000) {
          return 'AI prompt must be less than 1000 characters';
        }
        return '';
      
      default:
        return '';
    }
  };

  const validateForm = () => {
    const errors = {};
    Object.keys(formData).forEach(field => {
      if (field !== 'is_active' && field !== 'sort_order') { // Skip validation for switch and sort_order
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

  // Filtered topics based on search and filters
  const filteredTopics = useMemo(() => {
    return topics.filter(topic => {
      // Search filter
      const matchesSearch = searchQuery === '' || 
        topic.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (topic.description && topic.description.toLowerCase().includes(searchQuery.toLowerCase()));
      
      // Status filter
      const matchesStatus = statusFilter === 'all' || 
        (statusFilter === 'active' && topic.is_active) ||
        (statusFilter === 'inactive' && !topic.is_active);
      
      return matchesSearch && matchesStatus;
    });
  }, [topics, searchQuery, statusFilter]);

  const handleClickOpen = () => {
    setEditingTopic(null);
    setFormData({
      name: '',
      description: '',
      emoji: '📝',
      is_active: true,
      ai_prompt: '',
      sort_order: 0
    });
    setFormErrors({});
    setTouched({});
    setOpen(true);
  };

  const handleEdit = (topic) => {
    setEditingTopic(topic);
    setFormData({
      name: topic.name,
      description: topic.description || '',
      emoji: topic.emoji || '📝',
      is_active: topic.is_active,
      ai_prompt: topic.ai_prompt || '',
      sort_order: topic.sort_order || 0
    });
    setFormErrors({});
    setTouched({});
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setEditingTopic(null);
    setFormData({
      name: '',
      description: '',
      emoji: '📝',
      is_active: true,
      ai_prompt: '',
      sort_order: 0
    });
    setFormErrors({});
    setTouched({});
  };

  const handleSave = async () => {
    // Mark all fields as touched for validation display
    setTouched({
      name: true,
      description: true,
      emoji: true,
      ai_prompt: true
    });

    if (!validateForm()) {
      return; // Don't save if validation fails
    }

    try {
      setSaving(true);
      
      if (editingTopic) {
        // Update existing topic
        await apiService.updateCategory(editingTopic.id, formData);
      } else {
        // Add new topic
        await apiService.createCategory(formData);
      }
      
      // Reload topics from API
      await loadTopics();
      handleClose();
      setError(null);
    } catch (err) {
      setError(`Failed to save topic: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteClick = (topic) => {
    setTopicToDelete(topic);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (topicToDelete) {
      try {
        setSaving(true);
        await apiService.deleteCategory(topicToDelete.id);
        await loadTopics();
        setDeleteDialogOpen(false);
        setTopicToDelete(null);
        setError(null);
      } catch (err) {
        setError(`Failed to delete topic: ${err.message}`);
      } finally {
        setSaving(false);
      }
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setTopicToDelete(null);
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setStatusFilter('all');
  };

  const isFormValid = Object.keys(formErrors).every(key => !formErrors[key]) && 
                     formData.name.trim();

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
            Topics Management
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Управление темами для дайджестов
          </Typography>
        </div>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleClickOpen}
        >
          Add Topic
        </Button>
      </Box>

      {/* Search and Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Search topics by name, description, or keywords..."
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
          <Grid item xs={12} md={3}>
            <FormControl fullWidth variant="outlined">
              <InputLabel>Status Filter</InputLabel>
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                label="Status Filter"
                startAdornment={
                  <InputAdornment position="start">
                    <FilterIcon color="action" />
                  </InputAdornment>
                }
              >
                <MenuItem value="all">All Topics</MenuItem>
                <MenuItem value="active">Active Only</MenuItem>
                <MenuItem value="inactive">Inactive Only</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <Button 
              variant="outlined" 
              onClick={handleClearFilters}
              fullWidth
            >
              Clear Filters
            </Button>
          </Grid>
        </Grid>
        
        {/* Results info */}
        <Box mt={2}>
          <Typography variant="body2" color="textSecondary">
            Showing {filteredTopics.length} of {topics.length} topics
            {searchQuery && ` (filtered by "${searchQuery}")`}
            {statusFilter !== 'all' && ` (${statusFilter} only)`}
          </Typography>
        </Box>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Emoji</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredTopics.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                  <Typography variant="body1" color="textSecondary">
                    {searchQuery || statusFilter !== 'all' 
                      ? 'No topics match your search criteria' 
                      : 'No topics found'
                    }
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredTopics.map((topic) => (
                <TableRow key={topic.id}>
                  <TableCell component="th" scope="row">
                    <Typography variant="subtitle2">
                      {topic.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {topic.description || 'No description'}
                  </TableCell>
                  <TableCell>
                    <Typography variant="h6">
                      {topic.emoji || '📝'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={topic.is_active ? 'Active' : 'Inactive'}
                      color={topic.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton onClick={() => handleEdit(topic)} size="small">
                      <EditIcon />
                    </IconButton>
                    <IconButton 
                      onClick={() => handleDeleteClick(topic)} 
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
          {editingTopic ? 'Edit Topic' : 'Add New Topic'}
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
            label="Topic Name"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => handleFieldChange('name', e.target.value)}
            onBlur={() => handleFieldBlur('name')}
            error={touched.name && !!formErrors.name}
            helperText={touched.name && formErrors.name}
            sx={{ mb: 2 }}
            required
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
            helperText={touched.description && formErrors.description ? formErrors.description : 'Provide a clear description of what this topic covers'}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Emoji"
            fullWidth
            variant="outlined"
            value={formData.emoji}
            onChange={(e) => handleFieldChange('emoji', e.target.value)}
            onBlur={() => handleFieldBlur('emoji')}
            error={touched.emoji && !!formErrors.emoji}
            helperText={touched.emoji && formErrors.emoji ? formErrors.emoji : 'Choose an emoji for this topic (e.g., 💻, 🚀, 📈)'}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="AI Prompt"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={formData.ai_prompt}
            onChange={(e) => handleFieldChange('ai_prompt', e.target.value)}
            onBlur={() => handleFieldBlur('ai_prompt')}
            error={touched.ai_prompt && !!formErrors.ai_prompt}
            helperText={touched.ai_prompt && formErrors.ai_prompt ? formErrors.ai_prompt : 'Custom AI prompt for processing posts in this topic (optional)'}
            sx={{ mb: 2 }}
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
          <Button onClick={handleClose} disabled={saving}>Cancel</Button>
          <Button 
            onClick={handleSave} 
            variant="contained"
            disabled={!isFormValid || saving}
            startIcon={saving ? <CircularProgress size={20} /> : null}
          >
            {saving ? 'Saving...' : (editingTopic ? 'Update' : 'Create')}
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
            Are you sure you want to delete the topic <strong>"{topicToDelete?.name}"</strong>?
          </DialogContentText>
          <DialogContentText sx={{ mt: 2, color: 'warning.main' }}>
            <strong>Warning:</strong> This action cannot be undone. All channels associated with this topic will be unlinked.
          </DialogContentText>
          {topicToDelete && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="body2" color="textSecondary">
                Topic details:
              </Typography>
              <Typography variant="body2">
                • Description: {topicToDelete.description || 'No description'}
              </Typography>
              <Typography variant="body2">
                • Status: {topicToDelete.is_active ? 'Active' : 'Inactive'}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} disabled={saving}>
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteConfirm} 
            variant="contained" 
            color="error"
            disabled={saving}
            startIcon={saving ? <CircularProgress size={20} /> : <DeleteIcon />}
          >
            {saving ? 'Deleting...' : 'Delete Topic'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 