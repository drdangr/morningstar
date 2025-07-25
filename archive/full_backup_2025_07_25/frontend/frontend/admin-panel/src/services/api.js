const API_BASE_URL = '/api';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Network error' }));
        console.error(`API Error ${response.status}:`, errorData);
        console.error('Request URL:', url);
        console.error('Request body:', config.body);
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Health check
  async healthCheck() {
    return this.request('/health');
  }

  // Statistics
  async getStats() {
    return this.request('/stats');
  }

  // Categories (Topics) API
  async getCategories(params = {}) {
    const searchParams = new URLSearchParams();
    
    if (params.search) searchParams.append('search', params.search);
    if (params.active_only) searchParams.append('active_only', params.active_only);
    if (params.skip) searchParams.append('skip', params.skip);
    if (params.limit) searchParams.append('limit', params.limit);

    const queryString = searchParams.toString();
    const endpoint = queryString ? `/categories?${queryString}` : '/categories';
    
    return this.request(endpoint);
  }

  async getCategory(id) {
    return this.request(`/categories/${id}`);
  }

  async createCategory(categoryData) {
    return this.request('/categories', {
      method: 'POST',
      body: JSON.stringify(categoryData),
    });
  }

  async updateCategory(id, categoryData) {
    return this.request(`/categories/${id}`, {
      method: 'PUT',
      body: JSON.stringify(categoryData),
    });
  }

  async deleteCategory(id) {
    return this.request(`/categories/${id}`, {
      method: 'DELETE',
    });
  }

  // Channels API
  async getChannels(params = {}) {
    const searchParams = new URLSearchParams();
    
    if (params.search) searchParams.append('search', params.search);
    if (params.active_only) searchParams.append('active_only', params.active_only);
    if (params.skip) searchParams.append('skip', params.skip);
    if (params.limit) searchParams.append('limit', params.limit);

    const queryString = searchParams.toString();
    const endpoint = queryString ? `/channels?${queryString}` : '/channels';
    
    return this.request(endpoint);
  }

  async getChannel(id) {
    return this.request(`/channels/${id}`);
  }

  async createChannel(channelData) {
    return this.request('/channels', {
      method: 'POST',
      body: JSON.stringify(channelData),
    });
  }

  async updateChannel(id, channelData) {
    return this.request(`/channels/${id}`, {
      method: 'PUT',
      body: JSON.stringify(channelData),
    });
  }

  async deleteChannel(id) {
    return this.request(`/channels/${id}`, {
      method: 'DELETE',
    });
  }

  // Channel-Category relationships API
  async getChannelCategories(channelId) {
    return this.request(`/channels/${channelId}/categories`);
  }

  async addCategoryToChannel(channelId, categoryId) {
    return this.request(`/channels/${channelId}/categories/${categoryId}`, {
      method: 'POST',
    });
  }

  async removeCategoryFromChannel(channelId, categoryId) {
    return this.request(`/channels/${channelId}/categories/${categoryId}`, {
      method: 'DELETE',
    });
  }

  async getCategoryChannels(categoryId) {
    return this.request(`/categories/${categoryId}/channels`);
  }

  // Generic GET/POST/PUT/DELETE methods for custom endpoints
  async get(endpoint) {
    return this.request(endpoint);
  }

  async post(endpoint, data = null) {
    const options = {
      method: 'POST',
    };
    
    if (data) {
      options.body = JSON.stringify(data);
    }
    
    return this.request(endpoint, options);
  }

  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete(endpoint) {
    return this.request(endpoint, {
      method: 'DELETE',
    });
  }

  // === МУЛЬТИТЕНАНТНАЯ ОЧИСТКА ДАННЫХ ===
  
  // Предварительный просмотр очистки
  async getCleanupPreview(cleanupType, targetId = null) {
    const params = new URLSearchParams({ cleanup_type: cleanupType });
    if (targetId) {
      params.append('target_id', targetId);
    }
    return this.request(`/data/cleanup-preview?${params.toString()}`);
  }
  
  // Полная очистка всех данных
  async clearAllData(options = {}) {
    const params = new URLSearchParams({ confirm: true });
    if (options.includePosts !== undefined) {
      params.append('include_posts', options.includePosts);
    }
    if (options.includeAiResults !== undefined) {
      params.append('include_ai_results', options.includeAiResults);
    }
    return this.request(`/data/clear-all?${params.toString()}`, {
      method: 'DELETE',
    });
  }
  
  // Очистка данных по каналу
  async clearDataByChannel(channelId, options = {}) {
    const params = new URLSearchParams({ confirm: true });
    if (options.includePosts !== undefined) {
      params.append('include_posts', options.includePosts);
    }
    if (options.includeAiResults !== undefined) {
      params.append('include_ai_results', options.includeAiResults);
    }
    return this.request(`/data/clear-by-channel/${channelId}?${params.toString()}`, {
      method: 'DELETE',
    });
  }
  
  // Очистка данных по боту
  async clearDataByBot(botId, options = {}) {
    const params = new URLSearchParams({ confirm: true });
    if (options.includePosts !== undefined) {
      params.append('include_posts', options.includePosts);
    }
    if (options.includeAiResults !== undefined) {
      params.append('include_ai_results', options.includeAiResults);
    }
    return this.request(`/data/clear-by-bot/${botId}?${params.toString()}`, {
      method: 'DELETE',
    });
  }
  
  // === КОНЕЦ МУЛЬТИТЕНАНТНОЙ ОЧИСТКИ ДАННЫХ ===
}

// Create singleton instance
const apiService = new ApiService();

export default apiService;
export { apiService as dataAPI }; 