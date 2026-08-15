package xiaozhi.modules.config.service.impl;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Files;
import java.nio.file.Path;

import org.junit.jupiter.api.Test;

class HuoshanTtsAuthMigrationTest {

    @Test
    void migrationExposesCurrentAndLegacyAuthenticationWithoutSwitchingModels() throws Exception {
        String sql = Files.readString(Path.of("src/main/resources/db/changelog/202608151730.sql"));
        String master = Files.readString(Path.of("src/main/resources/db/changelog/db.changelog-master.yaml"));

        assertTrue(sql.contains("\"key\": \"api_key\""));
        assertTrue(sql.contains("X-Api-Key"));
        assertTrue(sql.contains("TTS_HuoshanDoubleStreamTTS"));
        assertTrue(sql.contains("TTS_HSDSTTS_V2"));
        assertTrue(sql.contains("迁移不切换现有模型或凭据"));
        assertTrue(master.contains("202608151730.sql"));
    }
}
