INSERT INTO `ai_model_provider`
    (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`,
     `creator`, `create_date`, `updater`, `update_date`)
SELECT
    'SYSTEM_PLUGIN_CYJDATA',
    'Plugin',
    'retrieve_from_cyjdata',
    '宠业家内部检索',
    '[{"key":"description","type":"string","label":"工具描述","default":"查询内部宠物商品、公开专业知识和课程目录。涉及选品、商品资料或自有语料时调用；资料不足时不要编造。","editing":false,"selected":false},{"key":"base_url","type":"string","label":"Retrieval Runtime 地址","default":"http://retrieval-runtime:8090","editing":false,"selected":false},{"key":"domains","type":"string","label":"检索范围","default":"product;publicKnowledge;courseCatalog","editing":false,"selected":false},{"key":"max_results","type":"number","label":"最多返回条数","default":4,"editing":false,"selected":false},{"key":"timeout_seconds","type":"number","label":"超时秒数","default":3.2,"editing":false,"selected":false}]',
    85,
    1,
    NOW(),
    1,
    NOW()
WHERE NOT EXISTS (
    SELECT 1
    FROM `ai_model_provider`
    WHERE `id` = 'SYSTEM_PLUGIN_CYJDATA'
       OR `provider_code` = 'retrieve_from_cyjdata'
);
