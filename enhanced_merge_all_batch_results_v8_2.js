console.log('🔗 Merging all ENHANCED batch results v8.2...');

// ИСПРАВЛЕНО: получаем данные от всех выполненных батчей через itemMatching
const originalData = $('Prepare Posts for Batching').all()[0]?.json;

// ИСПРАВЛЕНО: Собираем результаты батчей из NodeExecution storage
// В batch processing результаты сохраняются через $execution.customData
let allBatchResults = [];

// Попытка получить данные батчей через itemMatching
try {
    const processedBatchesResults = $execution.customData?.batchResults || [];
    allBatchResults = processedBatchesResults;
    console.log(`📊 Found ${allBatchResults.length} batch results from execution storage`);
} catch (error) {
    console.log('⚠️ Could not access execution storage, trying fallback method');
    
    // FALLBACK: пытаемся получить из Process Batch Results ноды
    try {
        const processBatchResults = $('Process Batch Results').all();
        allBatchResults = processBatchResults.map(item => item.json);
        console.log(`📊 FALLBACK: Found ${allBatchResults.length} batch results from Process Batch Results node`);
    } catch (fallbackError) {
        console.log('❌ Fallback failed, creating empty batch results array');
        allBatchResults = [];
    }
}

// ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: если нет результатов, пытаемся собрать из Split in Batches
if (allBatchResults.length === 0) {
    console.log('🔍 No batch results found, checking if we have itemMatching data...');
    
    // Проверяем есть ли в $input данные о батчах
    const inputData = $input.all();
    console.log(`📋 Input data contains ${inputData.length} items`);
    
    if (inputData.length > 0) {
        console.log('📋 First input item structure:', JSON.stringify(inputData[0], null, 2).substring(0, 500));
    }
}

// Собираем все AI результаты
let allAIAnalysis = [];
let totalProcessedPosts = 0;

allBatchResults.forEach((batchResult, index) => {
    const batchData = batchResult || {};
    console.log(`📦 ENHANCED Batch ${batchData.batch_index || index + 1}: ${(batchData.batch_results || []).length} results (parse_success: ${batchData.parse_success || false})`);
    
    const batchResults = batchData.batch_results || [];
    if (Array.isArray(batchResults)) {
        allAIAnalysis = allAIAnalysis.concat(batchResults);
    }
    
    totalProcessedPosts += batchData.batch_posts_count || 0;
});

console.log(`✅ Merged ${allAIAnalysis.length} ENHANCED AI results from ${allBatchResults.length} batches`);

// ИСПРАВЛЕНО: добавляем защиту от отсутствия данных
if (!originalData || !originalData.posts) {
    console.log('❌ КРИТИЧЕСКАЯ ОШИБКА: originalData отсутствует или некорректен');
    
    return {
        error: 'No original data found',
        timestamp: new Date().toISOString(),
        allBatchResults: allBatchResults.length,
        debugging_info: {
            originalDataExists: !!originalData,
            originalDataKeys: originalData ? Object.keys(originalData) : [],
            postsCount: originalData?.posts?.length || 0
        }
    };
}

// Группируем исходные посты по каналам
const posts = originalData.posts || [];
const channelsMetadata = originalData.channels_metadata || {};
const channelCategoryMap = originalData.channel_category_map || {};

const groupedPosts = {};
posts.forEach(post => {
    const key = post.channel_username || `channel_${post.channel_id}`;
    if (!groupedPosts[key]) {
        groupedPosts[key] = {
            channel_id: post.channel_id,
            channel_username: post.channel_username,
            channel_title: post.channel_title,
            posts: [],
            categories: channelsMetadata[post.channel_username]?.categories || []
        };
    }
    groupedPosts[key].posts.push(post);
});

// Применяем AI результаты к сгруппированным постам
const processedChannels = {};

Object.keys(groupedPosts).forEach(channelKey => {
    const channelData = groupedPosts[channelKey];
    const channelCategories = channelCategoryMap[channelData.channel_username] || [];
    
    const processedPosts = channelData.posts.map(post => {
        const analysis = allAIAnalysis.find(item => item.id == post.id);
        const isRelevant = analysis && analysis.summary && analysis.summary !== 'NULL';
        
        return {
            ...post,
            ai_summary: analysis?.summary || post.text?.substring(0, 150) + '...',
            ai_importance: analysis?.importance || 0,
            ai_urgency: analysis?.urgency || 0,
            ai_significance: analysis?.significance || 0,
            post_category: analysis?.category || 'Unknown',
            is_relevant: isRelevant,
            parsing_method: 'enhanced_v8.2_full_functionality'
        };
    });
    
    const relevantPosts = processedPosts.filter(post => post.is_relevant);
    
    relevantPosts.sort((a, b) => {
        const scoreA = a.ai_importance * 3 + a.ai_urgency * 2 + a.ai_significance * 2 + Math.log(a.views || 1);
        const scoreB = b.ai_importance * 3 + b.ai_urgency * 2 + b.ai_significance * 2 + Math.log(b.views || 1);
        return scoreB - scoreA;
    });
    
    if (relevantPosts.length > 0) {
        processedChannels[channelKey] = {
            ...channelData,
            posts: relevantPosts.slice(0, 8),
            all_processed_posts: processedPosts.length,
            relevant_posts: relevantPosts.length,
            ai_processed: true,
            channel_categories: channelCategories.map(c => c.name)
        };
    }
    
    console.log(`📊 ${channelData.channel_title}: ${processedPosts.length} → ${relevantPosts.length} relevant`);
});

return {
    timestamp: originalData.timestamp || new Date().toISOString(),
    processed_at: new Date().toISOString(),
    stats: originalData.collection_stats || {},
    processed_channels: processedChannels,
    total_channels: Object.keys(processedChannels).length,
    ai_analysis_stats: {
        total_analyzed: allAIAnalysis.length,
        relevant_posts: Object.values(processedChannels).reduce((sum, ch) => sum + ch.relevant_posts, 0),
        batches_processed: allBatchResults.length,
        total_posts_processed: totalProcessedPosts,
        avg_importance: allAIAnalysis.reduce((sum, item) => sum + (item.importance || 0), 0) / Math.max(allAIAnalysis.length, 1),
        avg_urgency: allAIAnalysis.reduce((sum, item) => sum + (item.urgency || 0), 0) / Math.max(allAIAnalysis.length, 1),
        avg_significance: allAIAnalysis.reduce((sum, item) => sum + (item.significance || 0), 0) / Math.max(allAIAnalysis.length, 1)
    },
    batch_processing_applied: true,
    enhanced_functionality: {
        custom_instructions_applied: originalData.custom_instructions ? true : false,
        category_ai_prompts_count: Object.keys(originalData.category_ai_prompts || {}).length,
        categories_with_prompts: Object.keys(originalData.category_ai_prompts || {})
    },
    debugging_info: {
        original_posts: posts.length,
        batch_results_found: allBatchResults.length,
        ai_analysis_items: allAIAnalysis.length,
        channels_with_relevant_posts: Object.keys(processedChannels).length
    },
    relevance_parsing_version: 'v8.2_enhanced_full_functionality_fixed'
}; 