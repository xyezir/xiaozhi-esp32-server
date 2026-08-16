package xiaozhi.modules.agent.support;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

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
