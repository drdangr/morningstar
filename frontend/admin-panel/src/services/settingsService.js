const API_BASE_URL = '/api';

export const settingsService = {
  // Получить все настройки с фильтрацией
  async getSettings(category = null, editableOnly = false) {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (editableOnly) params.append('editable_only', 'true');
    
    const response = await fetch(`${API_BASE_URL}/settings?${params}`);
    if (!response.ok) {
      throw new Error('Ошибка при получении настроек');
    }
    return response.json();
  },

  // Получить настройку по ID
  async getSetting(id) {
    const response = await fetch(`${API_BASE_URL}/settings/${id}`);
    if (!response.ok) {
      throw new Error('Настройка не найдена');
    }
    return response.json();
  },

  // Создать новую настройку
  async createSetting(settingData) {
    const response = await fetch(`${API_BASE_URL}/settings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settingData),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Ошибка при создании настройки');
    }
    return response.json();
  },

  // Обновить настройку
  async updateSetting(id, settingData) {
    const response = await fetch(`${API_BASE_URL}/settings/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settingData),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Ошибка при обновлении настройки');
    }
    return response.json();
  },

  // Удалить настройку
  async deleteSetting(id) {
    const response = await fetch(`${API_BASE_URL}/settings/${id}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Ошибка при удалении настройки');
    }
    return response.json();
  },

  // Получить все категории настроек
  async getCategories() {
    const response = await fetch(`${API_BASE_URL}/settings/categories`);
    if (!response.ok) {
      throw new Error('Ошибка при получении категорий');
    }
    return response.json();
  },

  // Получить значение конфигурации через ConfigManager
  async getConfigValue(key) {
    const response = await fetch(`${API_BASE_URL}/config/${key}`);
    if (!response.ok) {
      throw new Error('Конфигурация не найдена');
    }
    return response.json();
  },
}; 