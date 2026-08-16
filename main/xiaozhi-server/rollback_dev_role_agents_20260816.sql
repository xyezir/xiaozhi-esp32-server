-- Scoped runtime rollback for the 2026-08-16 development/test role rollout.
-- This intentionally keeps the Liquibase schema in place. Use the verified
-- pre-rollout database backup only when a full database restore is required.

SET NAMES utf8mb4;
START TRANSACTION;

SET @source_id := (
    SELECT id
    FROM ai_agent
    WHERE agent_code = 'AGT_1772292663798'
    LIMIT 1
);
SET @target_count := (
    SELECT COUNT(*)
    FROM ai_agent
    WHERE agent_code IN (
        'AGT_ROLE_CHEESE_20260816',
        'AGT_ROLE_BETA_20260816',
        'AGT_ROLE_NEZUKO_20260816'
    )
);
SET @device_count := (SELECT COUNT(*) FROM ai_device);
SET @safe_to_rollback := (
    @source_id IS NOT NULL
    AND @target_count = 3
    AND @device_count = 1
);

UPDATE ai_device
SET agent_id = @source_id,
    update_date = NOW()
WHERE @safe_to_rollback;

DELETE FROM ai_agent
WHERE @safe_to_rollback
  AND agent_code IN (
      'AGT_ROLE_CHEESE_20260816',
      'AGT_ROLE_BETA_20260816',
      'AGT_ROLE_NEZUKO_20260816'
  );

UPDATE ai_agent
SET role_code = NULL,
    role_avatar_url = NULL,
    role_theme_json = NULL,
    role_asset_version = NULL,
    role_asset_url = NULL,
    role_asset_sha256 = NULL,
    role_asset_size = NULL,
    role_distribution = 'public',
    role_wake_word = NULL,
    role_wake_model = NULL,
    updated_at = NOW()
WHERE @safe_to_rollback
  AND id = @source_id;

DELETE FROM sys_params
WHERE @safe_to_rollback
  AND param_code = 'role.internal.enabled';

SET @rollback_valid := (
    @safe_to_rollback
    AND (SELECT COUNT(*) FROM ai_agent WHERE id = @source_id AND role_code IS NULL) = 1
    AND (SELECT COUNT(*) FROM ai_agent WHERE agent_code IN (
        'AGT_ROLE_CHEESE_20260816',
        'AGT_ROLE_BETA_20260816',
        'AGT_ROLE_NEZUKO_20260816'
    )) = 0
    AND (SELECT COUNT(*) FROM ai_device WHERE agent_id = @source_id) = 1
    AND (SELECT COUNT(*) FROM sys_params WHERE param_code = 'role.internal.enabled') = 0
);
SET @transaction_action := IF(@rollback_valid, 'COMMIT', 'ROLLBACK');
PREPARE rollback_statement FROM @transaction_action;
EXECUTE rollback_statement;
DEALLOCATE PREPARE rollback_statement;

SELECT IF(@rollback_valid, 'PASS', 'ROLLBACK') AS rollback_result;
