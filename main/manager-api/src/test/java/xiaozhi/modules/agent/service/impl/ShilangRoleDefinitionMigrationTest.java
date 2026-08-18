package xiaozhi.modules.agent.service.impl;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Files;
import java.nio.file.Path;

import org.junit.jupiter.api.Test;

class ShilangRoleDefinitionMigrationTest {

    @Test
    void handbookRefreshKeepsPromptUtf8AndPreservesFullSpokenIdentifiers() throws Exception {
        String sql = Files.readString(Path.of("src/main/resources/db/changelog/202608190930.sql"));
        String master = Files.readString(Path.of("src/main/resources/db/changelog/db.changelog-master.yaml"));

        assertTrue(sql.contains("宠业家四郎"));
        assertTrue(sql.contains("retrieve_from_cyjdata"));
        assertTrue(sql.contains("亚宠展"));
        assertTrue(sql.contains("不得把品牌名、公司名、展馆号、展位号"));
        assertFalse(sql.contains("ã€"));
        assertTrue(sql.contains("UPDATE `ai_agent`"));
        assertTrue(sql.contains("UPDATE `ai_agent_template`"));
        assertTrue(master.contains("202608190930.sql"));
    }
}
