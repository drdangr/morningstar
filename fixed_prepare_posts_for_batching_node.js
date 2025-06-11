console.log('🤖 Preparing all posts for AI batching...');
const data = $json;
const posts = data.posts || [];
const channelsMetadata = data.channels_metadata || {};

// Собираем активные категории из метаданных каналов
const allActiveCategories = new Set();
const channelCategoryMap = {};
const categoryDescriptions = {};

Object.keys(channelsMetadata).forEach(channelUsername => {
    const channelData = channelsMetadata[channelUsername];
    if (channelData.categories && Array.isArray(channelData.categories)) {
        const activeCategories = channelData.categories.filter(cat => cat.is_active);
        channelCategoryMap[channelUsername] = activeCategories;
        
        activeCategories.forEach(category => {
            allActiveCategories.add(category.name);
            if (category.description) {
                categoryDescriptions[category.name] = category.description;
            }
        });
    }
});

const categories = Array.from(allActiveCategories);

// Формируем промпт
const topicsDescription = categories.map(cat => {
    const description = categoryDescriptions[cat] || cat;
    return `${cat} (${description})`;
}).join(', ');

const dynamicPrompt = `Отфильтруй посты по темам: ${topicsDescription}.

Правило: summary = "NULL" если текст поста НЕ имеет отношения НИ К ОДНОЙ из перечисленных тем.

Возвращай JSON: {"results": [{"id": "post_id", "summary": "резюме или NULL", "importance": 8, "urgency": 6, "significance": 7, "category": "Точное название темы"}]}

ВАЖНО: category должно быть одним из: ${categories.join(', ')} или "NULL"

Анализируй по СМЫСЛУ.`;

console.log(`📝 Prepared ${posts.length} posts for batching`);

return {
    timestamp: data.timestamp,
    collection_stats: data.collection_stats,
    channels_metadata: channelsMetadata,
    posts: posts,
    total_posts: posts.length,
    dynamic_prompt: dynamicPrompt,
    categories: categories,
    channel_category_map: channelCategoryMap,
    batch_processing: true,
    version: 'v8.1_fixed_categories_endpoint'
}; 