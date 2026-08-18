UPDATE `ai_model_provider`
SET `fields` = '[{"key":"appid","type":"string","label":"应用ID"},{"key":"access_token","type":"string","label":"访问令牌"},{"key":"boosting_table_name","type":"string","label":"热词文件名称"},{"key":"correct_table_name","type":"string","label":"替换词文件名称"},{"key":"output_dir","type":"string","label":"输出目录"},{"key":"end_window_size","type":"number","label":"静音判定时长(ms)"},{"key":"enable_multilingual","type":"boolean","label":"是否开启多语种识别模式"},{"key":"language","type":"string","label":"指定语言编码"},{"key":"resource_id","type":"string","label":"资源ID"}]',
    `update_date` = NOW()
WHERE `id` = 'SYSTEM_ASR_DoubaoStreamASR';

UPDATE `ai_model_config`
SET `config_json` = JSON_REMOVE(`config_json`, '$.api_key')
WHERE `id` = 'ASR_DoubaoStreamASRV2';
