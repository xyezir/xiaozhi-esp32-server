package xiaozhi.modules.agent.support;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;

import org.junit.jupiter.api.Test;

class RoleWakeProfileContractTest {
    @Test
    void blankPairPreservesLegacyBehavior() {
        RoleWakeProfileContract.Validation result = RoleWakeProfileContract.validate("  ", null);

        assertTrue(result.valid());
        assertFalse(result.configured());
        assertNull(result.wakeWord());
        assertNull(result.wakeModel());
    }

    @Test
    void completePairIsNormalized() {
        RoleWakeProfileContract.Validation result = RoleWakeProfileContract.validate(
                "  你好小智 ", " wn9_nihaoxiaozhi_tts ");

        assertTrue(result.valid());
        assertTrue(result.configured());
        assertEquals("你好小智", result.wakeWord());
        assertEquals("wn9_nihaoxiaozhi_tts", result.wakeModel());
        assertEquals(RoleWakeProfileContract.MODE_TRAINED, result.wakeMode());
        assertEquals(1L, result.wakeConfigVersion());
    }

    @Test
    void dynamicChineseProfileIsNormalized() {
        RoleWakeProfileContract.Validation result = RoleWakeProfileContract.validate(
                " dynamic ", " 你好四郎 ", " mn5q8_cn ",
                "  ni   hao si lang  ", " cn ", new BigDecimal("0.2154"), 7L);

        assertTrue(result.valid());
        assertTrue(result.configured());
        assertEquals("dynamic", result.wakeMode());
        assertEquals("你好四郎", result.wakeWord());
        assertEquals("mn5q8_cn", result.wakeModel());
        assertEquals("ni hao si lang", result.wakeCommand());
        assertEquals("cn", result.wakeLanguage());
        assertEquals(new BigDecimal("0.215"), result.wakeThreshold());
        assertEquals(7L, result.wakeConfigVersion());
    }

    @Test
    void invalidDynamicProfilesAreRejected() {
        assertFalse(RoleWakeProfileContract.validate(
                "dynamic", "你好四郎", "wn9_test", "ni hao si lang", "cn",
                new BigDecimal("0.2"), 1L).valid());
        assertFalse(RoleWakeProfileContract.validate(
                "dynamic", "你好四郎", "mn5q8_cn", "你好四郎", "cn",
                new BigDecimal("0.2"), 1L).valid());
        assertFalse(RoleWakeProfileContract.validate(
                "dynamic", "Hey cheese", "mn5q8_en", "hey cheese", "en",
                new BigDecimal("0.2"), 1L).valid());
        assertFalse(RoleWakeProfileContract.validate(
                "dynamic", "Hey 起司", "mn5q8_cn", "Hey qi si", "cn",
                new BigDecimal("0.2"), 1L).valid());
        assertFalse(RoleWakeProfileContract.validate(
                "dynamic", "你好四郎", "mn5q8_cn", "ni hao si lang", "cn",
                new BigDecimal("0.049"), 1L).valid());
        assertFalse(RoleWakeProfileContract.validate(
                "dynamic", "你好四郎", "mn5q8_cn", "ni hao si lang", "cn",
                new BigDecimal("0.2"), 0L).valid());
    }

    @Test
    void configVersionMatchesFirmwareUint32Boundary() {
        assertTrue(RoleWakeProfileContract.validate(
                "dynamic", "你好四郎", "mn5q8_cn", "ni hao si lang", "cn",
                new BigDecimal("0.2"), 4294967295L).valid());
        assertFalse(RoleWakeProfileContract.validate(
                "dynamic", "你好四郎", "mn5q8_cn", "ni hao si lang", "cn",
                new BigDecimal("0.2"), 4294967296L).valid());
    }

    @Test
    void partialOrUnsafePairIsRejected() {
        assertFalse(RoleWakeProfileContract.validate("你好四郎", null).valid());
        assertFalse(RoleWakeProfileContract.validateAtomicUpdate("你好四郎", null).valid());
        assertFalse(RoleWakeProfileContract.validate("你好\n四郎", "wn9_test").valid());
        assertFalse(RoleWakeProfileContract.validate("你好四郎", "../model").valid());
        assertFalse(RoleWakeProfileContract.validate("好".repeat(33), "wn9_test").valid());
    }
}
