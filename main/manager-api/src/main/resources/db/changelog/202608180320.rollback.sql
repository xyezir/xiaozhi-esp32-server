UPDATE `ai_model_provider`
SET `fields` = '[{"key":"enable_user_profile","type":"boolean","label":"启用用户画像"},{"key":"llm_provider","type":"string","label":"LLM提供商"},{"key":"llm_api_key","type":"string","label":"LLM API密钥"},{"key":"llm_model","type":"string","label":"LLM模型"},{"key":"openai_base_url","type":"string","label":"OpenAI兼容地址"},{"key":"embedding_provider","type":"string","label":"Embedding提供商"},{"key":"embedding_api_key","type":"string","label":"Embedding API密钥"},{"key":"embedding_model","type":"string","label":"Embedding模型"},{"key":"embedding_openai_base_url","type":"string","label":"Embedding OpenAI兼容地址"},{"key":"embedding_dims","type":"integer","label":"Embedding维度"},{"key":"vector_store","type":"dict","label":"向量存储配置(JSON)"}]',
    `update_date` = NOW()
WHERE `id` = 'SYSTEM_Memory_powermem';

UPDATE `ai_model_config`
SET `config_json` = JSON_REMOVE(
        `config_json`,
        '$.search_limit',
        '$.query_timeout_seconds',
        '$.save_timeout_seconds',
        '$.max_context_chars',
        '$.profile_max_chars',
        '$.memory_max_chars',
        '$.save_message_limit',
        '$.save_message_max_chars',
        '$.vector_store.config.database_path',
        '$.vector_store.config.collection_name',
        '$.vector_store.config.embedding_model_dims',
        '$.vector_store.config.enable_wal',
        '$.vector_store.config.timeout'
    ),
    `update_date` = NOW()
WHERE `id` = 'Memory_powermem';
