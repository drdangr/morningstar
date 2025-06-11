// Быстрый патч для CategoriesPage.jsx
// Замени строки 234-238 в функции handleSave на:

if (editingCategory) {
  // Update existing category
  const apiData = { ...formData, category_name: formData.name };
  delete apiData.name;
  await apiService.updateCategory(editingCategory.id, apiData);
} else {
  // Add new category  
  const apiData = { ...formData, category_name: formData.name };
  delete apiData.name;
  await apiService.createCategory(apiData);
} 