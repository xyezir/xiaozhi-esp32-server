-- 为火山双向流式 TTS 增加新版豆包语音控制台 API Key 鉴权。
-- 新版 api_key 与旧版 appid/access_token 二选一；迁移不切换现有模型或凭据。

UPDATE `ai_model_provider`
SET `fields` = '[
  {"key": "ws_url", "type": "string", "label": "WebSocket地址"},
  {"key": "api_key", "type": "string", "label": "新版豆包语音 API Key"},
  {"key": "appid", "type": "string", "label": "旧版应用ID"},
  {"key": "access_token", "type": "string", "label": "旧版访问令牌"},
  {"key": "resource_id", "type": "string", "label": "资源ID"},
  {"key": "speaker", "type": "string", "label": "默认音色"},
  {"key": "enable_ws_reuse", "type": "boolean", "label": "是否开启链接复用", "default": true},
  {"key": "audio_params", "type": "dict", "label": "音频输出配置"},
  {"key": "additions", "type": "dict", "label": "高级文本处理配置"},
  {"key": "mix_speaker", "type": "dict", "label": "混音控制配置"}
]'
WHERE `id` = 'SYSTEM_TTS_HSDSTTS';

UPDATE `ai_model_config`
SET `config_json` = JSON_SET(`config_json`, '$.api_key', '')
WHERE `id` IN ('TTS_HuoshanDoubleStreamTTS', 'TTS_HSDSTTS_V2')
  AND JSON_EXTRACT(`config_json`, '$.api_key') IS NULL;

UPDATE `ai_model_config`
SET `remark` = CONCAT(
  '鉴权说明：新版豆包语音控制台只填写 API Key，服务端发送 X-Api-Key；',
  '旧版控制台填写 AppID 与 Access Token。两种方式二选一，API Key 优先。',
  '豆包语音 API Key 与火山方舟 LLM API Key 不是同一配置项。\n\n',
  COALESCE(`remark`, '')
)
WHERE `id` IN ('TTS_HuoshanDoubleStreamTTS', 'TTS_HSDSTTS_V2')
  AND (`remark` IS NULL OR `remark` NOT LIKE '%X-Api-Key%');

-- rollback:
-- UPDATE ai_model_provider SET fields = JSON_REMOVE(fields, '$[1]') WHERE id = 'SYSTEM_TTS_HSDSTTS';
-- UPDATE ai_model_config SET config_json = JSON_REMOVE(config_json, '$.api_key') WHERE id IN ('TTS_HuoshanDoubleStreamTTS', 'TTS_HSDSTTS_V2');
