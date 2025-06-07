import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Switch,
  FormControlLabel,
  Alert,
  Snackbar,
  CircularProgress,
  Tooltip
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Settings as SettingsIcon,
  Storage as StorageIcon,
  Psychology as AiIcon,
  Schedule as ScheduleIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { settingsService } from '../services/settingsService';

// Иконки для категорий
const categoryIcons = {
  system: <SettingsIcon />,
  digest: <ScheduleIcon />,
  ai: <AiIcon />,
  storage: <StorageIcon />
};

// Переводы категорий
const categoryLabels = {
  system: 'Система',
  digest: 'Дайджесты',
  ai: 'Искусственный интеллект',
  storage: 'Хранилище'
};

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const SettingsPage = () => {
  const [settings, setSettings] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [tabValue, setTabValue] = useState(0);
  
  // Диалоги
  const [editDialog, setEditDialog] = useState(false);
  const [addDialog, setAddDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [selectedSetting, setSelectedSetting] = useState(null);
  
  // Форма
  const [formData, setFormData] = useState({
    key: '',
    value: '',
    value_type: 'string',
    category: '',
    description: '',
    is_editable: true
  });

  // Загрузка данных
  const loadData = async () => {
    try {
      setLoading(true);
      const [settingsData, categoriesData] = await Promise.all([
        settingsService.getSettings(),
        settingsService.getCategories()
      ]);
      
      setSettings(settingsData);
      setCategories(categoriesData.categories || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Группировка настроек по категориям
  const groupedSettings = settings.reduce((acc, setting) => {
    const category = setting.category || 'other';
    if (!acc[category]) acc[category] = [];
    acc[category].push(setting);
    return acc;
  }, {});

  // Обработчики форм
  const handleEdit = (setting) => {
    setSelectedSetting(setting);
    setFormData({
      key: setting.key,
      value: setting.value || '',
      value_type: setting.value_type,
      category: setting.category || '',
      description: setting.description || '',
      is_editable: setting.is_editable
    });
    setEditDialog(true);
  };

  const handleAdd = () => {
    setFormData({
      key: '',
      value: '',
      value_type: 'string',
      category: categories[0] || '',
      description: '',
      is_editable: true
    });
    setAddDialog(true);
  };

  const handleDelete = (setting) => {
    setSelectedSetting(setting);
    setDeleteDialog(true);
  };

  const handleFormSubmit = async (isEdit = false) => {
    try {
      if (isEdit) {
        await settingsService.updateSetting(selectedSetting.id, {
          value: formData.value,
          description: formData.description,
          is_editable: formData.is_editable
        });
        setSuccess('Настройка успешно обновлена');
      } else {
        await settingsService.createSetting(formData);
        setSuccess('Настройка успешно создана');
      }
      
      setEditDialog(false);
      setAddDialog(false);
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteConfirm = async () => {
    try {
      await settingsService.deleteSetting(selectedSetting.id);
      setSuccess('Настройка успешно удалена');
      setDeleteDialog(false);
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  // Форматирование значений
  const formatValue = (value, valueType) => {
    if (!value) return '-';
    
    switch (valueType) {
      case 'boolean':
        return value === 'true' ? 'Да' : 'Нет';
      case 'json':
        try {
          return JSON.stringify(JSON.parse(value), null, 2);
        } catch {
          return value;
        }
      default:
        return value;
    }
  };

  // Получение текущей категории
  const getCurrentCategory = () => {
    const categoryKeys = Object.keys(groupedSettings);
    return categoryKeys[tabValue] || null;
  };

  const currentSettings = groupedSettings[getCurrentCategory()] || [];

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Заголовок */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Настройки системы
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadData}
            sx={{ mr: 2 }}
          >
            Обновить
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAdd}
          >
            Добавить настройку
          </Button>
        </Box>
      </Box>

      {/* Описание */}
      <Alert severity="info" sx={{ mb: 3 }}>
        Здесь можно управлять настройками системы. Критически важные настройки (API ключи, токены) 
        хранятся в .env файле и не отображаются в админ-панели.
      </Alert>

      {/* Вкладки по категориям */}
      <Card>
        <Tabs
          value={tabValue}
          onChange={(e, newValue) => setTabValue(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          {Object.keys(groupedSettings).map((category, index) => (
            <Tab
              key={category}
              icon={categoryIcons[category] || <SettingsIcon />}
              label={`${categoryLabels[category] || category} (${groupedSettings[category].length})`}
              iconPosition="start"
            />
          ))}
        </Tabs>

        {/* Содержимое вкладок */}
        {Object.keys(groupedSettings).map((category, index) => (
          <TabPanel key={category} value={tabValue} index={index}>
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Ключ</TableCell>
                    <TableCell>Значение</TableCell>
                    <TableCell>Тип</TableCell>
                    <TableCell>Описание</TableCell>
                    <TableCell>Редактируемая</TableCell>
                    <TableCell align="center">Действия</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {groupedSettings[category].map((setting) => (
                    <TableRow key={setting.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {setting.key}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            maxWidth: 200, 
                            overflow: 'hidden', 
                            textOverflow: 'ellipsis',
                            fontFamily: setting.value_type === 'json' ? 'monospace' : 'inherit'
                          }}
                        >
                          {formatValue(setting.value, setting.value_type)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={setting.value_type} 
                          size="small" 
                          color="primary"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {setting.description || 'Нет описания'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={setting.is_editable ? 'Да' : 'Нет'} 
                          size="small"
                          color={setting.is_editable ? 'success' : 'default'}
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="Редактировать">
                          <IconButton
                            size="small"
                            onClick={() => handleEdit(setting)}
                            disabled={!setting.is_editable}
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Удалить">
                          <IconButton
                            size="small"
                            onClick={() => handleDelete(setting)}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                  {groupedSettings[category].length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} align="center">
                        <Typography variant="body2" color="text.secondary">
                          Нет настроек в этой категории
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>
        ))}
      </Card>

      {/* Диалог редактирования */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Редактировать настройку</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Ключ"
            value={formData.key}
            disabled
            sx={{ mb: 2, mt: 1 }}
          />
          
          {formData.value_type === 'boolean' ? (
            <FormControlLabel
              control={
                <Switch
                  checked={formData.value === 'true'}
                  onChange={(e) => setFormData({
                    ...formData,
                    value: e.target.checked ? 'true' : 'false'
                  })}
                />
              }
              label="Значение"
              sx={{ mb: 2 }}
            />
          ) : (
            <TextField
              fullWidth
              label="Значение"
              value={formData.value}
              onChange={(e) => setFormData({ ...formData, value: e.target.value })}
              multiline={formData.value_type === 'json'}
              rows={formData.value_type === 'json' ? 4 : 1}
              sx={{ mb: 2 }}
            />
          )}

          <TextField
            fullWidth
            label="Описание"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            multiline
            rows={2}
            sx={{ mb: 2 }}
          />

          <FormControlLabel
            control={
              <Switch
                checked={formData.is_editable}
                onChange={(e) => setFormData({ ...formData, is_editable: e.target.checked })}
              />
            }
            label="Разрешить редактирование"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>Отмена</Button>
          <Button 
            onClick={() => handleFormSubmit(true)}
            variant="contained"
          >
            Сохранить
          </Button>
        </DialogActions>
      </Dialog>

      {/* Диалог добавления */}
      <Dialog open={addDialog} onClose={() => setAddDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Добавить настройку</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Ключ"
            value={formData.key}
            onChange={(e) => setFormData({ ...formData, key: e.target.value.toUpperCase() })}
            sx={{ mb: 2, mt: 1 }}
            helperText="Используйте ЗАГЛАВНЫЕ_БУКВЫ_С_ПОДЧЕРКИВАНИЕМ"
          />

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Тип значения</InputLabel>
            <Select
              value={formData.value_type}
              onChange={(e) => setFormData({ ...formData, value_type: e.target.value })}
              label="Тип значения"
            >
              <MenuItem value="string">Строка</MenuItem>
              <MenuItem value="integer">Целое число</MenuItem>
              <MenuItem value="float">Дробное число</MenuItem>
              <MenuItem value="boolean">Логическое значение</MenuItem>
              <MenuItem value="json">JSON</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Категория</InputLabel>
            <Select
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              label="Категория"
            >
              {categories.map((cat) => (
                <MenuItem key={cat} value={cat}>
                  {categoryLabels[cat] || cat}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {formData.value_type === 'boolean' ? (
            <FormControlLabel
              control={
                <Switch
                  checked={formData.value === 'true'}
                  onChange={(e) => setFormData({
                    ...formData,
                    value: e.target.checked ? 'true' : 'false'
                  })}
                />
              }
              label="Значение"
              sx={{ mb: 2 }}
            />
          ) : (
            <TextField
              fullWidth
              label="Значение"
              value={formData.value}
              onChange={(e) => setFormData({ ...formData, value: e.target.value })}
              multiline={formData.value_type === 'json'}
              rows={formData.value_type === 'json' ? 4 : 1}
              sx={{ mb: 2 }}
            />
          )}

          <TextField
            fullWidth
            label="Описание"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            multiline
            rows={2}
            sx={{ mb: 2 }}
          />

          <FormControlLabel
            control={
              <Switch
                checked={formData.is_editable}
                onChange={(e) => setFormData({ ...formData, is_editable: e.target.checked })}
              />
            }
            label="Разрешить редактирование"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialog(false)}>Отмена</Button>
          <Button 
            onClick={() => handleFormSubmit(false)}
            variant="contained"
          >
            Создать
          </Button>
        </DialogActions>
      </Dialog>

      {/* Диалог удаления */}
      <Dialog open={deleteDialog} onClose={() => setDeleteDialog(false)}>
        <DialogTitle>Подтвердите удаление</DialogTitle>
        <DialogContent>
          <Typography>
            Вы уверены, что хотите удалить настройку{' '}
            <strong>{selectedSetting?.key}</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Это действие нельзя отменить.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog(false)}>Отмена</Button>
          <Button 
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
          >
            Удалить
          </Button>
        </DialogActions>
      </Dialog>

      {/* Уведомления */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError('')}
      >
        <Alert severity="error" onClose={() => setError('')}>
          {error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!success}
        autoHideDuration={4000}
        onClose={() => setSuccess('')}
      >
        <Alert severity="success" onClose={() => setSuccess('')}>
          {success}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SettingsPage; 