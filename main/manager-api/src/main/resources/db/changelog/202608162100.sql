-- Add Volcengine large-model flash file ASR using the new speech-console API Key.
-- This is intentionally a separate provider from the legacy AppID/Access Token
-- streaming driver so existing installations are not silently reinterpreted.

DELETE FROM `ai_model_provider` WHERE `id` = 'SYSTEM_ASR_DoubaoFlashASR';
INSERT INTO `ai_model_provider`
    (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`)
VALUES
    (
        'SYSTEM_ASR_DoubaoFlashASR',
        'ASR',
        'doubao_flash',
        '豆包大模型极速语音识别(API Key)',
        '[{"key":"api_key","label":"新版豆包语音 API Key","type":"password"},{"key":"resource_id","label":"资源ID（固定）","type":"string"},{"key":"request_timeout","label":"请求超时（秒）","type":"number"},{"key":"enable_itn","label":"启用文本规范化","type":"boolean"},{"key":"output_dir","label":"输出目录","type":"string"}]',
        19,
        1,
        NOW(),
        1,
        NOW()
    );

DELETE FROM `ai_model_config` WHERE `id` = 'ASR_DoubaoFlashASR';
INSERT INTO `ai_model_config`
VALUES
    (
        'ASR_DoubaoFlashASR',
        'ASR',
        'DoubaoFlashASR',
        '豆包大模型录音文件极速版',
        0,
        1,
        '{"type":"doubao_flash","api_key":"","resource_id":"volc.bigasr.auc_turbo","request_timeout":20,"enable_itn":true,"output_dir":"tmp/"}',
        'https://www.volcengine.com/docs/6561/1631584',
        '使用新版豆包语音控制台 API Key，以 X-Api-Key 调用录音文件极速识别接口。资源ID固定为 volc.bigasr.auc_turbo。该模型是整句非流式识别，与需要 AppID/Access Token 的豆包流式语音识别是两个独立接口。',
        19,
        NULL,
        NULL,
        NULL,
        NULL
    );
