ALTER TABLE `ai_agent_template`
    DROP COLUMN `role_wake_config_version`,
    DROP COLUMN `role_wake_threshold`,
    DROP COLUMN `role_wake_language`,
    DROP COLUMN `role_wake_command`,
    DROP COLUMN `role_wake_mode`;

ALTER TABLE `ai_agent`
    DROP COLUMN `role_wake_config_version`,
    DROP COLUMN `role_wake_threshold`,
    DROP COLUMN `role_wake_language`,
    DROP COLUMN `role_wake_command`,
    DROP COLUMN `role_wake_mode`;
