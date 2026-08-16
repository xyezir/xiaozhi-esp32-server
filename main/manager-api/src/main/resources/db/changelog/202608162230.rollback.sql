ALTER TABLE `ai_agent_template`
    DROP COLUMN `role_wake_model`,
    DROP COLUMN `role_wake_word`;

ALTER TABLE `ai_agent`
    DROP COLUMN `role_wake_model`,
    DROP COLUMN `role_wake_word`;
