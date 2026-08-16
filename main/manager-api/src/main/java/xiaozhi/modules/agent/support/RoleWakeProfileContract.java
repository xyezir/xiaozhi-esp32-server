package xiaozhi.modules.agent.support;

import java.util.regex.Pattern;

import org.apache.commons.lang3.StringUtils;

/**
 * Validates the role wake profile as one atomic runtime contract.
 *
 * <p>The displayed phrase is never sufficient on its own: a profile is active
 * only when both the phrase and the packed WakeNet model identifier are
 * present. Two blank values intentionally represent a legacy role package,
 * which keeps the firmware's last-known-good wake model.</p>
 */
public final class RoleWakeProfileContract {
    private static final int MAX_WAKE_WORD_CODE_POINTS = 32;
    private static final Pattern MODEL_ID = Pattern.compile("^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$");

    private RoleWakeProfileContract() {
    }

    public static Validation validate(String wakeWord, String wakeModel) {
        String normalizedWord = normalize(wakeWord);
        String normalizedModel = normalize(wakeModel);
        boolean hasWord = normalizedWord != null;
        boolean hasModel = normalizedModel != null;
        if (hasWord != hasModel) {
            return Validation.invalid("唤醒短语和 WakeNet 模型必须同时配置或同时清空");
        }
        if (!hasWord) {
            return Validation.legacy();
        }
        if (normalizedWord.codePointCount(0, normalizedWord.length()) > MAX_WAKE_WORD_CODE_POINTS
                || normalizedWord.codePoints().anyMatch(RoleWakeProfileContract::isUnsafeCodePoint)) {
            return Validation.invalid("唤醒短语最长 32 个字符，且不能包含控制字符");
        }
        if (!MODEL_ID.matcher(normalizedModel).matches()) {
            return Validation.invalid("WakeNet 模型标识只能使用字母、数字、点、下划线和短横线，且最长 96 位");
        }
        return Validation.active(normalizedWord, normalizedModel);
    }

    public static Validation validateAtomicUpdate(String wakeWord, String wakeModel) {
        if ((wakeWord == null) != (wakeModel == null)) {
            return Validation.invalid("更新角色唤醒配置时必须同时提交唤醒短语和 WakeNet 模型");
        }
        return validate(wakeWord, wakeModel);
    }

    public static String normalize(String value) {
        String normalized = StringUtils.trimToNull(value);
        return normalized == null ? null : normalized;
    }

    private static boolean isUnsafeCodePoint(int codePoint) {
        return Character.isISOControl(codePoint)
                || codePoint == Character.LINE_SEPARATOR
                || codePoint == Character.PARAGRAPH_SEPARATOR;
    }

    public record Validation(boolean valid, boolean configured, String wakeWord, String wakeModel, String error) {
        private static Validation invalid(String error) {
            return new Validation(false, false, null, null, error);
        }

        private static Validation legacy() {
            return new Validation(true, false, null, null, null);
        }

        private static Validation active(String wakeWord, String wakeModel) {
            return new Validation(true, true, wakeWord, wakeModel, null);
        }
    }
}
