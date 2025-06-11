/* ПОЛНОЕ ИСПРАВЛЕНИЕ КАТЕГОРИЙ - ЗАМЕНЫ ДЛЯ CategoriesPage.jsx */

// 1. ИСПРАВИТЬ loadCategories (строки 72-82):
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

// 2. ИСПРАВЛЕНИЕ УЖЕ ГОТОВО в handleSave (преобразование name -> category_name)

// 3. Все остальные места (category.name, поиск, валидация) будут работать
//    так как мы преобразуем category_name -> name при загрузке

/* ИТОГО: 
   - Backend использует category_name
   - Frontend всегда использует name  
   - При загрузке: category_name -> name
   - При отправке: name -> category_name
*/ 