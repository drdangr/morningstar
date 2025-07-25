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

export default function CategoriesPage() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [open, setOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [categoryToDelete, setCategoryToDelete] = useState(null);
  
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
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      setLoading(true);
      const data = await apiService.getCategories();
      
      // Transform backend data (category_name -> name for frontend)
      const transformedData = data.map(category => ({
        ...category,
        name: category.category_name || category.name || ''
      }));
      
      setCategories(transformedData);
      setError(null);
    } catch (err) {
      setError('Failed to load categories: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Validation rules
  const validateField = (name, value) => {
    switch (name) {
      case 'name':
        if (!value || value.trim().length < 2) {
          return 'Category name must be at least 2 characters long';
        }
        if (value.trim().length > 50) {
          return 'Category name must be less than 50 characters';
        }
        // Check for duplicate names (excluding current editing category)
        const isDuplicate = categories.some(category => 
          category.name && category.name.toLowerCase() === value.trim().toLowerCase() && 
          category.id !== editingCategory?.id
        );
        if (isDuplicate) {
          return 'A category with this name already exists';
        }
        return '';
      
      case 'description':
        if (value && value.trim().length > 500) {
          return 'Description must be less than 500 characters';
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

  // Filtered categories based on search and filters
  const filteredCategories = useMemo(() => {
    const filtered = categories.filter(category => {
      // Search filter
      const matchesSearch = searchQuery === '' || 
        (category.name && category.name.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (category.description && category.description.toLowerCase().includes(searchQuery.toLowerCase()));
      
      // Status filter
      const matchesStatus = statusFilter === 'all' || 
        (statusFilter === 'active' && category.is_active) ||
        (statusFilter === 'inactive' && !category.is_active);
      
      return matchesSearch && matchesStatus;
    });
    
    // Sort by sort_order first, then by name
    return filtered.sort((a, b) => {
      if (a.sort_order !== b.sort_order) {
        return (a.sort_order || 0) - (b.sort_order || 0);
      }
      return a.name.localeCompare(b.name);
    });
  }, [categories, searchQuery, statusFilter]);

  const handleClickOpen = () => {
    setEditingCategory(null);
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

  const handleEdit = (category) => {
    setEditingCategory(category);
    setFormData({
      name: category.name,
      description: category.description || '',
      emoji: category.emoji || '📝',
      is_active: category.is_active,
      ai_prompt: category.ai_prompt || '',
      sort_order: category.sort_order || 0
    });
    setFormErrors({});
    setTouched({});
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setEditingCategory(null);
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
      ai_prompt: true
    });

    if (!validateForm()) {
      return; // Don't save if validation fails
    }

    try {
      setSaving(true);
      
      // Отправляем данные как есть, без трансформации
      const apiData = {
        name: formData.name,
        description: formData.description,
        emoji: formData.emoji,
        is_active: formData.is_active,
        ai_prompt: formData.ai_prompt,
        sort_order: formData.sort_order
      };

      console.log('Sending data to API:', apiData);
      console.log('Category ID:', editingCategory?.id);

      if (editingCategory) {
        // Update existing category
        await apiService.updateCategory(editingCategory.id, apiData);
      } else {
        // Add new category
        await apiService.createCategory(apiData);
      }
      
      // Reload categories from API
      await loadCategories();
      handleClose();
      setError(null);
    } catch (err) {
      setError(`Failed to save category: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteClick = (category) => {
    setCategoryToDelete(category);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (categoryToDelete) {
      try {
        setSaving(true);
        await apiService.deleteCategory(categoryToDelete.id);
        await loadCategories();
        setDeleteDialogOpen(false);
        setCategoryToDelete(null);
        setError(null);
      } catch (err) {
        setError(`Failed to delete category: ${err.message}`);
      } finally {
        setSaving(false);
      }
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setCategoryToDelete(null);
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
            Categories Management
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Управление категориями для дайджестов
          </Typography>
        </div>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleClickOpen}
        >
          Add Category
        </Button>
      </Box>

      {/* Search and Filter Controls */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search categories by name, description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={6} md={2}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="all">All Categories</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="inactive">Inactive</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={6} md={2}>
            <Button
              variant="outlined"
              onClick={handleClearFilters}
              startIcon={<FilterIcon />}
              disabled={searchQuery === '' && statusFilter === 'all'}
            >
              Clear
            </Button>
          </Grid>
          <Grid item xs={12} md={2}>
            <Typography variant="body2" color="textSecondary">
              Showing {filteredCategories.length} of {categories.length} categories
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredCategories.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  <Typography variant="body2" color="textSecondary">
                    {searchQuery || statusFilter !== 'all' 
                      ? 'No categories match your search criteria'
                      : 'No categories found'
                    }
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredCategories.map((category) => (
                <TableRow key={category.id}>
                  <TableCell component="th" scope="row">
                    <Typography variant="subtitle2">
                      {category.emoji} {category.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {category.description || 'No description'}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={category.is_active ? 'Active' : 'Inactive'}
                      color={category.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton onClick={() => handleEdit(category)} size="small">
                      <EditIcon />
                    </IconButton>
                    <IconButton 
                      onClick={() => handleDeleteClick(category)} 
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
      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingCategory ? 'Edit Category' : 'Add Category'}
        </DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 1 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={8}>
                <TextField
                  fullWidth
                  label="Category Name"
                  value={formData.name}
                  onChange={(e) => handleFieldChange('name', e.target.value)}
                  onBlur={() => handleFieldBlur('name')}
                  error={!!formErrors.name}
                  helperText={formErrors.name}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Description"
                  value={formData.description}
                  onChange={(e) => handleFieldChange('description', e.target.value)}
                  onBlur={() => handleFieldBlur('description')}
                  error={!!formErrors.description}
                  helperText={formErrors.description || 'Brief description of this category'}
                  multiline
                  rows={2}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Emoji"
                  value={formData.emoji}
                  onChange={(e) => handleFieldChange('emoji', e.target.value)}
                  helperText="Emoji icon for this category"
                  inputProps={{ maxLength: 10 }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Sort Order"
                  type="number"
                  value={formData.sort_order}
                  onChange={(e) => handleFieldChange('sort_order', parseInt(e.target.value) || 0)}
                  helperText="Lower numbers appear first"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="AI Prompt"
                  value={formData.ai_prompt}
                  onChange={(e) => handleFieldChange('ai_prompt', e.target.value)}
                  onBlur={() => handleFieldBlur('ai_prompt')}
                  error={!!formErrors.ai_prompt}
                  helperText={formErrors.ai_prompt || 'AI instructions for categorizing posts'}
                  multiline
                  rows={3}
                />
              </Grid>
              <Grid item xs={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.is_active}
                      onChange={(e) => handleFieldChange('is_active', e.target.checked)}
                    />
                  }
                  label="Active"
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={saving}>
            Cancel
          </Button>
          <Button 
            onClick={handleSave} 
            variant="contained" 
            disabled={!isFormValid || saving}
            startIcon={saving ? <CircularProgress size={20} /> : null}
          >
            {saving ? 'Saving...' : (editingCategory ? 'Update' : 'Create')}
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
            Are you sure you want to delete the category <strong>"{categoryToDelete?.name}"</strong>?
          </DialogContentText>
          <DialogContentText sx={{ mt: 2, color: 'warning.main' }}>
            <strong>Warning:</strong> This action cannot be undone. All channels associated with this category will be unlinked.
          </DialogContentText>
          {categoryToDelete && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="body2" color="textSecondary">
                Category details:
              </Typography>
              <Typography variant="body2">
                • Description: {categoryToDelete.description || 'No description'}
              </Typography>
              <Typography variant="body2">
                • Status: {categoryToDelete.is_active ? 'Active' : 'Inactive'}
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
            {saving ? 'Deleting...' : 'Delete Category'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 