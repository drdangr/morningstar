const openAIResponse = $json;

// ИСПРАВЛЕНО: получаем batchData из предыдущей ноды напрямую
const prepareBatchNode = $('Prepare Batch for AI').first();
const batchData = prepareBatchNode?.json;

console.log(`📝 Processing ENHANCED OpenAI response for batch ${batchData?.batch_index || 'unknown'}`);

let aiAnalysis = [];
let parseSuccess = false;

// ИСПРАВЛЕННЫЙ ПАРСИНГ - проверяем правильную структуру [0].message.content
if (Array.isArray(openAIResponse) && openAIResponse[0]?.message?.content) {
    const contentString = openAIResponse[0].message.content;
    console.log(`🔍 Found content string, length: ${contentString.length}`);
    
    try {
        const parsed = JSON.parse(contentString);
        aiAnalysis = parsed.results || [];
        parseSuccess = true;
        console.log(`✅ Successfully parsed from [0].message.content: ${aiAnalysis.length} results`);
    } catch (error) {
        console.log('⚠️ Failed to parse [0].message.content as JSON:', error.message);
        
        // Попытка исправить обрезанный JSON
        try {
            let fixedContent = contentString;
            if (!fixedContent.endsWith('}]}}') && !fixedContent.endsWith('}]}')) {
                const openBraces = (fixedContent.match(/{/g) || []).length;
                const closeBraces = (fixedContent.match(/}/g) || []).length;
                const openBrackets = (fixedContent.match(/\[/g) || []).length;
                const closeBrackets = (fixedContent.match(/\]/g) || []).length;
                
                for (let i = 0; i < openBraces - closeBraces; i++) {
                    fixedContent += '}';
                }
                for (let i = 0; i < openBrackets - closeBrackets; i++) {
                    fixedContent += ']';
                }
                
                console.log(`🔧 Attempting to fix truncated JSON...`);
                const fixedParsed = JSON.parse(fixedContent);
                aiAnalysis = fixedParsed.results || [];
                parseSuccess = true;
                console.log(`✅ Fixed truncated JSON: ${aiAnalysis.length} results`);
            }
        } catch (fixError) {
            console.log('❌ Failed to fix truncated JSON:', fixError.message);
        }
    }
}

// Fallback для других структур
if (!parseSuccess) {
    if (openAIResponse.message?.content?.results) {
        aiAnalysis = openAIResponse.message.content.results;
        console.log(`✅ Found results in message.content.results: ${aiAnalysis.length}`);
    } else if (openAIResponse.message?.content && typeof openAIResponse.message.content === 'string') {
        try {
            const parsed = JSON.parse(openAIResponse.message.content);
            aiAnalysis = parsed.results || parsed;
            console.log(`✅ Parsed from string content: ${aiAnalysis.length}`);
        } catch (error) {
            console.log('⚠️ Failed to parse string content:', error.message);
        }
    }
}

console.log(`✅ ENHANCED Batch ${batchData?.batch_index || 'unknown'} processed: ${aiAnalysis.length} AI results`);

// ИСПРАВЛЕНО: добавляем batch_uuid для правильной идентификации
const batchUuid = `batch_${batchData?.batch_index || $runIndex + 1}_${Date.now()}`;

// Сохраняем результаты батча для последующего слияния
return {
    batch_uuid: batchUuid,
    batch_index: batchData?.batch_index || $runIndex + 1,
    batch_results: aiAnalysis,
    batch_posts_count: batchData?.total_posts_in_batch || 0,
    processed_at: new Date().toISOString(),
    parse_success: parseSuccess,
    channels_metadata: batchData?.channels_metadata,
    channel_category_map: batchData?.channel_category_map,
    category_descriptions: batchData?.category_descriptions,
    category_ai_prompts: batchData?.category_ai_prompts,
    custom_instructions: batchData?.custom_instructions,
    total_batches: batchData?.total_batches,
    posts_for_ai_count: (batchData?.posts_for_ai || []).length
}; 