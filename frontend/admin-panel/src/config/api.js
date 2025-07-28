// Централизованная конфигурация API
// В production режиме (Nginx) используем относительные пути через прокси
// В development (localhost) используем прямое подключение к Backend API

export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 
  (typeof window !== 'undefined' && window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : '');

// Вспомогательная функция для создания полного URL
export const createApiUrl = (endpoint) => {
  // Убираем лишние слеши и добавляем /api префикс если нужно
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const apiPrefix = cleanEndpoint.startsWith('/api') ? '' : '/api';
  return `${API_BASE_URL}${apiPrefix}${cleanEndpoint}`;
};

// Готовые endpoint builders
export const apiEndpoints = {
  publicBots: () => createApiUrl('/api/public-bots'),
  publicBot: (id) => createApiUrl(`/api/public-bots/${id}`),
  botChannels: (botId) => createApiUrl(`/api/public-bots/${botId}/channels`),
  botCategories: (botId) => createApiUrl(`/api/public-bots/${botId}/categories`),
  botTemplates: () => createApiUrl('/api/bot-templates'),
  channels: () => createApiUrl('/api/channels'),
  categories: () => createApiUrl('/api/categories'),
}; 