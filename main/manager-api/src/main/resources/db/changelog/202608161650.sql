ALTER TABLE `ai_agent_template`
    ADD COLUMN `role_code` varchar(64) DEFAULT NULL COMMENT '设备角色稳定标识' AFTER `system_prompt`,
    ADD COLUMN `role_avatar_url` varchar(512) DEFAULT NULL COMMENT '角色预览图' AFTER `role_code`,
    ADD COLUMN `role_theme_json` text DEFAULT NULL COMMENT '角色主题JSON' AFTER `role_avatar_url`,
    ADD COLUMN `role_asset_version` varchar(64) DEFAULT NULL COMMENT '角色资源版本' AFTER `role_theme_json`,
    ADD COLUMN `role_asset_url` varchar(1024) DEFAULT NULL COMMENT '角色资源下载地址' AFTER `role_asset_version`,
    ADD COLUMN `role_asset_sha256` char(64) DEFAULT NULL COMMENT '角色资源SHA-256' AFTER `role_asset_url`,
    ADD COLUMN `role_asset_size` bigint unsigned DEFAULT NULL COMMENT '角色资源字节数' AFTER `role_asset_sha256`,
    ADD COLUMN `role_distribution` varchar(32) NOT NULL DEFAULT 'public' COMMENT 'public/internal-only' AFTER `role_asset_size`;

ALTER TABLE `ai_agent`
    ADD COLUMN `role_code` varchar(64) DEFAULT NULL COMMENT '设备角色稳定标识' AFTER `system_prompt`,
    ADD COLUMN `role_avatar_url` varchar(512) DEFAULT NULL COMMENT '角色预览图' AFTER `role_code`,
    ADD COLUMN `role_theme_json` text DEFAULT NULL COMMENT '角色主题JSON' AFTER `role_avatar_url`,
    ADD COLUMN `role_asset_version` varchar(64) DEFAULT NULL COMMENT '角色资源版本' AFTER `role_theme_json`,
    ADD COLUMN `role_asset_url` varchar(1024) DEFAULT NULL COMMENT '角色资源下载地址' AFTER `role_asset_version`,
    ADD COLUMN `role_asset_sha256` char(64) DEFAULT NULL COMMENT '角色资源SHA-256' AFTER `role_asset_url`,
    ADD COLUMN `role_asset_size` bigint unsigned DEFAULT NULL COMMENT '角色资源字节数' AFTER `role_asset_sha256`,
    ADD COLUMN `role_distribution` varchar(32) NOT NULL DEFAULT 'public' COMMENT 'public/internal-only' AFTER `role_asset_size`;
