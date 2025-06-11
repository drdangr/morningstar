// ВОССТАНОВЛЕННАЯ ФУНКЦИОНАЛЬНОСТЬ v8.2 - полный функционал старой ноды "Prepare for AI"
console.log('🤖 Preparing all posts for AI batching with FULL functionality v8.2...');
const data = $json;
const posts = data.posts || [];
const channelsMetadata = data.channels_metadata || {};

console.log(`📋 Found posts: ${posts.length}`);
console.log('📋 Channels metadata available:', Object.keys(channelsMetadata));

// ВОССТАНОВЛЕНО: Разделяем объекты для description и ai_prompt
const allActiveCategories = new Set();
const channelCategoryMap = {};
const categoryDescriptions = {}; // Для тем анализа (description поле)
const categoryAIPrompts = {};     // Для кастомных инструкций (ai_prompt поле)

Object.keys(channelsMetadata).forEach(channelUsername => {
    const channelData = channelsMetadata[channelUsername];
    console.log(`📋 Канал: ${channelData.title} (${channelUsername})`);
    
    if (channelData.categories && Array.isArray(channelData.categories)) {
        const activeCategories = channelData.categories.filter(cat => cat.is_active);
        channelCategoryMap[channelUsername] = activeCategories;
        
        activeCategories.forEach(category => {
            allActiveCategories.add(category.name);
            
            // ВОССТАНОВЛЕНО: правильно разделяем поля
            if (category.description) {
                categoryDescriptions[category.name] = category.description;
            }
            if (category.ai_prompt) {
                categoryAIPrompts[category.name] = category.ai_prompt;
            }
            
            console.log(`  🏷️ Активная категория: ${category.name}`);
            console.log(`    📝 Description: ${category.description?.substring(0, 50)}...`);
            console.log(`    🤖 AI Prompt: ${category.ai_prompt?.substring(0, 50)}...`);
        });
        
        if (activeCategories.length === 0) {
            console.log(`  ⚠️ Нет активных категорий для ${channelUsername}`);
        }
    }
});

const categories = Array.from(allActiveCategories);

console.log(`✅ RESTORED v8.2: Найдено ${categories.length} уникальных активных категорий:`, categories);
console.log('🔗 Связи каналов с категориями:');
Object.keys(channelCategoryMap).forEach(channel => {
    const cats = channelCategoryMap[channel].map(c => c.name).join(', ');
    console.log(`  ${channel} → [${cats}]`);
});

// ВОССТАНОВЛЕНО: Формируем описание тем из поля description
const topicsDescription = categories.map(cat => {
    const description = categoryDescriptions[cat] || cat;
    return `${cat} (${description})`;
}).join(', ');

// ВОССТАНОВЛЕНО: Формируем структурированные кастомные инструкции
const customInstructions = categories.map(cat => {
    const description = categoryDescriptions[cat] || cat;
    const aiPrompt = categoryAIPrompts[cat];
    if (aiPrompt) {
        return `для постов на тему '${cat} (${description})' учти инструкции: ${aiPrompt}`;
    }
    return null;
}).filter(instruction => instruction).join(', ');

// ВОССТАНОВЛЕНО: Улучшенный промпт с правильным разделением полей
let dynamicPrompt = `Отфильтруй посты по темам: ${topicsDescription}.

Правило: summary = "NULL" если текст поста НЕ имеет отношения НИ К ОДНОЙ из перечисленных тем.

Для каждого поста:

ЕСЛИ пост имеет отношение к теме - дай краткое резюме + метрики 1-10.
ЕСЛИ пост НЕ имеет отношения к темам - напиши "NULL" + метрики 0.

Возвращай JSON:
{"results": [{"id": "post_id", "summary": "резюме или NULL", "importance": 8, "urgency": 6, "significance": 7, "category": "Точное название темы"}]}

ВАЖНО:
- Поле "category" должно содержать ТОЧНОЕ название темы: ${categories.join(', ')}
- Выбирай НАИБОЛЕЕ ПОДХОДЯЩУЮ тему для каждого поста
- Для нерелевантных постов: category = "NULL"

Анализируй по СМЫСЛУ, а не только по ключевым словам. Учитывай контекст и семантику.`;

// ВОССТАНОВЛЕНО: Добавляем структурированные кастомные инструкции
if (customInstructions) {
    dynamicPrompt += `

Дополнительные инструкции: ${customInstructions}`;
    console.log('✅ Added RESTORED custom AI instructions from ai_prompt fields');
}

console.log('🔮 Generated RESTORED prompt v8.2 with topic-specific instructions');
console.log('📊 Categories for analysis (from description):', categories);
console.log('📊 Custom instructions (from ai_prompt):', Object.keys(categoryAIPrompts).length, 'found');
console.log('🎯 Topics description:', topicsDescription);
if (customInstructions) {
    console.log('🤖 Custom instructions:', customInstructions.substring(0, 200) + '...');
}

// FALLBACK только если вообще нет категорий
if (categories.length === 0) {
    console.log('❌ КРИТИЧЕСКАЯ ОШИБКА: Нет активных категорий, используем fallback');
    const fallbackPrompt = `Анализируй посты и определяй их релевантность общим новостным темам. Для релевантных постов давай краткое резюме и метрики важности/срочности/значимости, для нерелевантных - "NULL".`;
    
    return {
        timestamp: data.timestamp,
        collection_stats: data.collection_stats,
        channels_metadata: channelsMetadata,
        posts: posts,
        total_posts: posts.length,
        dynamic_prompt: fallbackPrompt,
        categories: ['Общие новости'],
        channel_category_map: {},
        category_descriptions: {},
        category_ai_prompts: {},
        error: 'No active categories found',
        batch_processing: true,
        version: 'v8.2_fallback'
    };
}

console.log(`📝 Prepared ${posts.length} posts for ENHANCED batching`);

return {
    timestamp: data.timestamp,
    collection_stats: data.collection_stats,
    channels_metadata: channelsMetadata,
    posts: posts,
    total_posts: posts.length,
    dynamic_prompt: dynamicPrompt,
    categories: categories,
    channel_category_map: channelCategoryMap,
    category_descriptions: categoryDescriptions,
    category_ai_prompts: categoryAIPrompts,
    topics_description: topicsDescription,
    custom_instructions: customInstructions,
    binary_relevance: true,
    with_metrics: true,
    batch_processing: true,
    version: 'v8.2_full_functionality_restored'
}; 