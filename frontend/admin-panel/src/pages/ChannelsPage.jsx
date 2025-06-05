import React, { useState, useMemo } from 'react';
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
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Telegram as TelegramIcon,
  Warning as WarningIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';

const mockChannels = [
  { 
    id: 1, 
    name: 'TechCrunch', 
    username: '@techcrunch', 
    description: 'Technology news and startup updates',
    topics: ['Technology'],
    active: true,
    subscribers: '2.1M'
  },
  { 
    id: 2, 
    name: 'CoinDesk', 
    username: '@coindesk', 
    description: 'Cryptocurrency and blockchain news',
    topics: ['Crypto'],
    active: true,
    subscribers: '890K'
  },
  { 
    id: 3, 
    name: 'Breaking News', 
    username: '@breakingnews', 
    description: 'General news updates',
    topics: ['Politics', 'World'],
    active: false,
    subscribers: '1.5M'
  },
];

// Get unique topics for filter dropdown
const getAllTopics = (channels) => {
  const topicsSet = new Set();
  channels.forEach(channel => {
    channel.topics.forEach(topic => topicsSet.add(topic));
  });
  return Array.from(topicsSet).sort();
};

export default function ChannelsPage() {
  const [channels, setChannels] = useState(mockChannels);
  const [open, setOpen] = useState(false);
  const [editingChannel, setEditingChannel] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [channelToDelete, setChannelToDelete] = useState(null);

  // Search and filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all'); // 'all', 'active', 'inactive'
  const [topicFilter, setTopicFilter] = useState('all'); // 'all' or specific topic

  // Form validation states
  const [formData, setFormData] = useState({
    name: '',
    username: '',
    description: '',
    topics: '',
    active: true
  });
  const [formErrors, setFormErrors] = useState({});
  const [touched, setTouched] = useState({});

  const allTopics = getAllTopics(channels);

  // Validation rules
  const validateField = (name, value) => {
    switch (name) {
      case 'name':
        if (!value || value.trim().length < 2) {
          return 'Channel name must be at least 2 characters long';
        }
        if (value.trim().length > 50) {
          return 'Channel name must be less than 50 characters';
        }
        // Check for duplicate names (excluding current editing channel)
        const isDuplicateName = channels.some(channel => 
          channel.name.toLowerCase() === value.trim().toLowerCase() && 
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
        if (!value || value.trim().length < 10) {
          return 'Description must be at least 10 characters long';
        }
        if (value.trim().length > 300) {
          return 'Description must be less than 300 characters';
        }
        return '';
      
      case 'topics':
        if (!value || value.trim().length === 0) {
          return 'At least one topic is required';
        }
        const topicsArray = value.split(',').map(t => t.trim()).filter(t => t);
        if (topicsArray.length === 0) {
          return 'At least one topic is required';
        }
        if (topicsArray.length > 5) {
          return 'Maximum 5 topics allowed';
        }
        // Check for topic length
        const hasLongTopics = topicsArray.some(t => t.length > 30);
        if (hasLongTopics) {
          return 'Each topic must be less than 30 characters';
        }
        return '';
      
      default:
        return '';
    }
  };

  const validateForm = () => {
    const errors = {};
    Object.keys(formData).forEach(field => {
      if (field !== 'active') { // Skip validation for switch
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
        channel.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        channel.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
        channel.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        channel.topics.some(topic => topic.toLowerCase().includes(searchQuery.toLowerCase()));
      
      // Status filter
      const matchesStatus = statusFilter === 'all' || 
        (statusFilter === 'active' && channel.active) ||
        (statusFilter === 'inactive' && !channel.active);
      
      // Topic filter
      const matchesTopic = topicFilter === 'all' || 
        channel.topics.includes(topicFilter);
      
      return matchesSearch && matchesStatus && matchesTopic;
    });
  }, [channels, searchQuery, statusFilter, topicFilter]);

  const handleClickOpen = () => {
    setEditingChannel(null);
    setFormData({
      name: '',
      username: '',
      description: '',
      topics: '',
      active: true
    });
    setFormErrors({});
    setTouched({});
    setOpen(true);
  };

  const handleEdit = (channel) => {
    setEditingChannel(channel);
    setFormData({
      name: channel.name,
      username: channel.username,
      description: channel.description,
      topics: channel.topics.join(', '),
      active: channel.active
    });
    setFormErrors({});
    setTouched({});
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setEditingChannel(null);
    setFormData({
      name: '',
      username: '',
      description: '',
      topics: '',
      active: true
    });
    setFormErrors({});
    setTouched({});
  };

  const handleSave = () => {
    // Mark all fields as touched for validation display
    setTouched({
      name: true,
      username: true,
      description: true,
      topics: true
    });

    if (!validateForm()) {
      return; // Don't save if validation fails
    }

    const topicsArray = formData.topics.split(',').map(t => t.trim()).filter(t => t);
    
    if (editingChannel) {
      // Update existing channel
      setChannels(prev => prev.map(channel => 
        channel.id === editingChannel.id 
          ? {
              ...channel,
              name: formData.name.trim(),
              username: formData.username.trim(),
              description: formData.description.trim(),
              topics: topicsArray,
              active: formData.active
            }
          : channel
      ));
    } else {
      // Add new channel
      const newChannel = {
        id: Math.max(...channels.map(c => c.id)) + 1,
        name: formData.name.trim(),
        username: formData.username.trim(),
        description: formData.description.trim(),
        topics: topicsArray,
        active: formData.active,
        subscribers: '0' // Default for new channels
      };
      setChannels(prev => [...prev, newChannel]);
    }
    
    handleClose();
  };

  const handleDeleteClick = (channel) => {
    setChannelToDelete(channel);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (channelToDelete) {
      setChannels(channels.filter(channel => channel.id !== channelToDelete.id));
      setDeleteDialogOpen(false);
      setChannelToDelete(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setChannelToDelete(null);
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setStatusFilter('all');
    setTopicFilter('all');
  };

  const isFormValid = Object.keys(formErrors).every(key => !formErrors[key]) && 
                     formData.name.trim() && 
                     formData.username.trim() && 
                     formData.description.trim() && 
                     formData.topics.trim();

  return (
    <Box>
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
          <Grid item xs={12} md={2}>
            <FormControl fullWidth variant="outlined">
              <InputLabel>Topic</InputLabel>
              <Select
                value={topicFilter}
                onChange={(e) => setTopicFilter(e.target.value)}
                label="Topic"
              >
                <MenuItem value="all">All Topics</MenuItem>
                {allTopics.map(topic => (
                  <MenuItem key={topic} value={topic}>{topic}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
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
            {topicFilter !== 'all' && ` (topic: ${topicFilter})`}
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
              <TableCell>Subscribers</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredChannels.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                  <Typography variant="body1" color="textSecondary">
                    {searchQuery || statusFilter !== 'all' || topicFilter !== 'all'
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
                          {channel.name}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          {channel.username}
                        </Typography>
                      </div>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {channel.description}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={1} flexWrap="wrap">
                      {channel.topics.map((topic, index) => (
                        <Chip
                          key={index}
                          label={topic}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {channel.subscribers}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={channel.active ? 'Active' : 'Inactive'}
                      color={channel.active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
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
            label="Channel Name"
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
            label="Username"
            fullWidth
            variant="outlined"
            value={formData.username}
            onChange={(e) => handleFieldChange('username', e.target.value)}
            onBlur={() => handleFieldBlur('username')}
            error={touched.username && !!formErrors.username}
            helperText={touched.username && formErrors.username ? formErrors.username : 'Telegram username with @ (e.g., @techcrunch)'}
            sx={{ mb: 2 }}
            required
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
            required
          />
          <TextField
            margin="dense"
            label="Topics"
            fullWidth
            variant="outlined"
            value={formData.topics}
            onChange={(e) => handleFieldChange('topics', e.target.value)}
            onBlur={() => handleFieldBlur('topics')}
            error={touched.topics && !!formErrors.topics}
            helperText={touched.topics && formErrors.topics ? formErrors.topics : 'Comma-separated topics this channel covers (e.g., Technology, AI, Startups)'}
            sx={{ mb: 2 }}
            required
          />
          <FormControlLabel
            control={
              <Switch 
                checked={formData.active} 
                onChange={(e) => handleFieldChange('active', e.target.checked)}
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
            Are you sure you want to delete the channel <strong>"{channelToDelete?.name}"</strong> ({channelToDelete?.username})?
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
                • Subscribers: {channelToDelete.subscribers}
              </Typography>
              <Typography variant="body2">
                • Topics: {channelToDelete.topics?.join(', ')}
              </Typography>
              <Typography variant="body2">
                • Status: {channelToDelete.active ? 'Active' : 'Inactive'}
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
    </Box>
  );
} 