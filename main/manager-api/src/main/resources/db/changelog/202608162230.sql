ALTER TABLE `ai_agent_template`
    ADD COLUMN `role_wake_word` varchar(128) DEFAULT NULL COMMENT '角色实际唤醒短语' AFTER `role_distribution`,
    ADD COLUMN `role_wake_model` varchar(96) DEFAULT NULL COMMENT '角色实际WakeNet模型标识' AFTER `role_wake_word`;

ALTER TABLE `ai_agent`
    ADD COLUMN `role_wake_word` varchar(128) DEFAULT NULL COMMENT '角色实际唤醒短语' AFTER `role_distribution`,
    ADD COLUMN `role_wake_model` varchar(96) DEFAULT NULL COMMENT '角色实际WakeNet模型标识' AFTER `role_wake_word`;

-- Existing hosted role packages all contain this exact WakeNet9 model. Seed
-- the actual capability, not the desired future role-specific phrase.
UPDATE `ai_agent_template`
SET `role_wake_word` = '你好小智',
    `role_wake_model` = 'wn9_nihaoxiaozhi_tts'
WHERE `role_code` IS NOT NULL
  AND `role_wake_word` IS NULL
  AND `role_wake_model` IS NULL;

UPDATE `ai_agent`
SET `role_wake_word` = '你好小智',
    `role_wake_model` = 'wn9_nihaoxiaozhi_tts'
WHERE `role_code` IS NOT NULL
  AND `role_wake_word` IS NULL
  AND `role_wake_model` IS NULL;
