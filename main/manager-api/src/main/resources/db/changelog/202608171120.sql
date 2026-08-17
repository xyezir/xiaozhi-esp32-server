ALTER TABLE `ai_agent_template`
    ADD COLUMN `role_wake_mode` varchar(16) DEFAULT NULL COMMENT '角色唤醒模式: trained/dynamic' AFTER `role_wake_model`,
    ADD COLUMN `role_wake_command` varchar(160) DEFAULT NULL COMMENT '动态唤醒声学命令' AFTER `role_wake_mode`,
    ADD COLUMN `role_wake_language` varchar(8) DEFAULT NULL COMMENT '动态唤醒语言: cn/en' AFTER `role_wake_command`,
    ADD COLUMN `role_wake_threshold` decimal(4,3) DEFAULT NULL COMMENT '动态唤醒检测阈值' AFTER `role_wake_language`,
    ADD COLUMN `role_wake_config_version` bigint DEFAULT NULL COMMENT '角色唤醒配置版本' AFTER `role_wake_threshold`;

ALTER TABLE `ai_agent`
    ADD COLUMN `role_wake_mode` varchar(16) DEFAULT NULL COMMENT '角色唤醒模式: trained/dynamic' AFTER `role_wake_model`,
    ADD COLUMN `role_wake_command` varchar(160) DEFAULT NULL COMMENT '动态唤醒声学命令' AFTER `role_wake_mode`,
    ADD COLUMN `role_wake_language` varchar(8) DEFAULT NULL COMMENT '动态唤醒语言: cn/en' AFTER `role_wake_command`,
    ADD COLUMN `role_wake_threshold` decimal(4,3) DEFAULT NULL COMMENT '动态唤醒检测阈值' AFTER `role_wake_language`,
    ADD COLUMN `role_wake_config_version` bigint DEFAULT NULL COMMENT '角色唤醒配置版本' AFTER `role_wake_threshold`;

UPDATE `ai_agent_template`
SET `role_wake_mode` = 'trained',
    `role_wake_config_version` = 1
WHERE `role_wake_word` IS NOT NULL
  AND `role_wake_model` IS NOT NULL
  AND `role_wake_mode` IS NULL;

UPDATE `ai_agent`
SET `role_wake_mode` = 'trained',
    `role_wake_config_version` = 1
WHERE `role_wake_word` IS NOT NULL
  AND `role_wake_model` IS NOT NULL
  AND `role_wake_mode` IS NULL;
