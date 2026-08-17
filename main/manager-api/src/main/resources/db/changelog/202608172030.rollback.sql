DELETE FROM `ai_agent_plugin_mapping`
WHERE `plugin_id` = 'SYSTEM_PLUGIN_CYJDATA';

DELETE FROM `ai_model_provider`
WHERE `id` = 'SYSTEM_PLUGIN_CYJDATA';
