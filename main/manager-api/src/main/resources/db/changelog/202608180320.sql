UPDATE `ai_model_provider`
SET `fields` = '[{"key":"enable_user_profile","type":"boolean","label":"启用用户画像"},{"key":"llm_provider","type":"string","label":"LLM提供商"},{"key":"llm_api_key","type":"string","label":"LLM API密钥"},{"key":"llm_model","type":"string","label":"LLM模型"},{"key":"openai_base_url","type":"string","label":"OpenAI兼容地址"},{"key":"embedding_provider","type":"string","label":"Embedding提供商"},{"key":"embedding_api_key","type":"string","label":"Embedding API密钥"},{"key":"embedding_model","type":"string","label":"Embedding模型"},{"key":"embedding_openai_base_url","type":"string","label":"Embedding OpenAI兼容地址"},{"key":"embedding_dims","type":"integer","label":"Embedding维度"},{"key":"vector_store","type":"dict","label":"向量存储配置(JSON)"},{"key":"search_limit","type":"integer","label":"召回条数"},{"key":"query_timeout_seconds","type":"number","label":"语音召回超时(秒)"},{"key":"save_timeout_seconds","type":"number","label":"异步保存超时(秒)"},{"key":"max_context_chars","type":"integer","label":"召回上下文最大字符"},{"key":"profile_max_chars","type":"integer","label":"用户画像最大字符"},{"key":"memory_max_chars","type":"integer","label":"单条记忆最大字符"},{"key":"save_message_limit","type":"integer","label":"每轮最多保存消息数"},{"key":"save_message_max_chars","type":"integer","label":"单条保存消息最大字符"}]',
    `update_date` = NOW()
WHERE `id` = 'SYSTEM_Memory_powermem';

UPDATE `ai_model_config`
SET `config_json` = JSON_INSERT(
        `config_json`,
        '$.vector_store.config.database_path', '/opt/xiaozhi-esp32-server/data/powermem/shilang.db',
        '$.vector_store.config.collection_name', 'shilang_memories',
        '$.vector_store.config.embedding_model_dims', 1024,
        '$.vector_store.config.enable_wal', TRUE,
        '$.vector_store.config.timeout', 30,
        '$.search_limit', 6,
        '$.query_timeout_seconds', 1.5,
        '$.save_timeout_seconds', 15.0,
        '$.max_context_chars', 1800,
        '$.profile_max_chars', 700,
        '$.memory_max_chars', 360,
        '$.save_message_limit', 12,
        '$.save_message_max_chars', 1200
    ),
    `update_date` = NOW()
WHERE `id` = 'Memory_powermem';
