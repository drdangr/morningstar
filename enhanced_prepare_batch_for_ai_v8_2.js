// ВОССТАНОВЛЕНА функциональность с категориями каналов v8.2
const currentBatch = $json;
const originalData = $('Prepare Posts for Batching').all()[0]?.json;
const batchIndex = $runIndex + 1;
const totalBatches = Math.ceil(originalData.total_posts / 30);

console.log(`🔄 Processing ENHANCED batch ${batchIndex}/${totalBatches}`);

// ВОССТАНОВЛЕНО: Подготавливаем текущий батч для AI с категориями каналов
const postsForAI = (Array.isArray(currentBatch) ? currentBatch : [currentBatch]).map(post => {
    // ВОССТАНОВЛЕНО: добавляем категории канала к каждому посту
    const channelUsername = post.channel_username;
    const channelCategories = originalData.channel_category_map[channelUsername]?.map(c => c.name) || [];
    
    return {
        id: post.id,
        text: post.text?.substring(0, 1000) || '',
        channel: post.channel_title,
        channel_username: channelUsername,
        views: post.views || 0,
        date: post.date,
        url: post.url,
        channel_categories: channelCategories // ВОССТАНОВЛЕНО: важное поле!
    };
}).filter(post => post.text.length > 10); // ИСПРАВЛЕНО: было 50, стало 10

console.log(`📊 ENHANCED Batch ${batchIndex}: ${(Array.isArray(currentBatch) ? currentBatch : [currentBatch]).length} input posts → ${postsForAI.length} after filter`);

// ВОССТАНОВЛЕНО: передаем все важные данные для AI
return {
    dynamic_prompt: originalData.dynamic_prompt,
    posts_for_ai: postsForAI,
    batch_index: batchIndex,
    total_batches: totalBatches,
    total_posts_in_batch: postsForAI.length,
    channels_metadata: originalData.channels_metadata,
    channel_category_map: originalData.channel_category_map,
    category_descriptions: originalData.category_descriptions,
    category_ai_prompts: originalData.category_ai_prompts,
    custom_instructions: originalData.custom_instructions,
    categories: originalData.categories
}; 