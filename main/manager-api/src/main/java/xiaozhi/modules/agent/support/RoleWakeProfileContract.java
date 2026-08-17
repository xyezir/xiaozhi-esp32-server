package xiaozhi.modules.agent.support;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Locale;
import java.util.regex.Pattern;

import org.apache.commons.lang3.StringUtils;

/** Validates and normalizes one atomic role wake profile. */
public final class RoleWakeProfileContract {
    public static final String MODE_TRAINED = "trained";
    public static final String MODE_DYNAMIC = "dynamic";
    public static final BigDecimal DEFAULT_DYNAMIC_THRESHOLD = new BigDecimal("0.200");
    public static final long DEFAULT_CONFIG_VERSION = 1L;
    public static final long MAX_CONFIG_VERSION = 0xFFFF_FFFFL;

    private static final int MAX_WAKE_WORD_CODE_POINTS = 32;
    private static final Pattern MODEL_ID = Pattern.compile("^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$");
    private static final Pattern CHINESE_COMMAND = Pattern.compile("^[a-z]+(?: [a-z]+){2,7}$");
    private static final BigDecimal MIN_THRESHOLD = new BigDecimal("0.050");
    private static final BigDecimal MAX_THRESHOLD = new BigDecimal("0.950");

    private RoleWakeProfileContract() {
    }

    /** Backward-compatible validation for the original WakeNet pair. */
    public static Validation validate(String wakeWord, String wakeModel) {
        String normalizedWord = normalize(wakeWord);
        String normalizedModel = normalize(wakeModel);
        if (normalizedWord == null && normalizedModel == null) {
            return Validation.legacy();
        }
        return validate(MODE_TRAINED, normalizedWord, normalizedModel,
                null, null, null, DEFAULT_CONFIG_VERSION);
    }

    public static Validation validate(String wakeMode, String wakeWord, String wakeModel,
            String wakeCommand, String wakeLanguage, BigDecimal wakeThreshold,
            Long wakeConfigVersion) {
        String mode = normalize(wakeMode);
        String word = normalize(wakeWord);
        String model = normalize(wakeModel);
        String command = normalizeSpaces(wakeCommand);
        String language = normalize(wakeLanguage);

        boolean anyConfigured = mode != null || word != null || model != null || command != null
                || language != null || wakeThreshold != null || wakeConfigVersion != null;
        if (!anyConfigured) {
            return Validation.legacy();
        }
        if (mode == null && word != null && model != null && command == null && language == null) {
            mode = MODE_TRAINED;
        }
        if (!(MODE_TRAINED.equals(mode) || MODE_DYNAMIC.equals(mode))) {
            return Validation.invalid("唤醒模式只能是 trained 或 dynamic");
        }
        if (word == null || model == null) {
            return Validation.invalid("唤醒短语、模式和模型必须作为完整配置提交");
        }
        if (word.codePointCount(0, word.length()) > MAX_WAKE_WORD_CODE_POINTS
                || word.codePoints().anyMatch(RoleWakeProfileContract::isUnsafeCodePoint)) {
            return Validation.invalid("唤醒短语最长 32 个字符，且不能包含控制字符");
        }
        if (!MODEL_ID.matcher(model).matches()) {
            return Validation.invalid("唤醒模型标识只能使用字母、数字、点、下划线和短横线，且最长 96 位");
        }
        long version = wakeConfigVersion == null ? DEFAULT_CONFIG_VERSION : wakeConfigVersion;
        if (version <= 0 || version > MAX_CONFIG_VERSION) {
            return Validation.invalid("唤醒配置版本必须在 1 到 4294967295 之间");
        }

        if (MODE_TRAINED.equals(mode)) {
            if (command != null || language != null || wakeThreshold != null) {
                return Validation.invalid("trained 模式不能携带动态命令、语言或阈值");
            }
            if (!model.startsWith("wn")) {
                return Validation.invalid("trained 模式必须使用 WakeNet 模型");
            }
            return Validation.active(mode, word, model, null, null, null, version);
        }

        if (!"mn5q8_cn".equals(model)) {
            return Validation.invalid("dynamic 模式当前只支持 mn5q8_cn 模型");
        }
        if (!"cn".equals(language)) {
            return Validation.invalid("dynamic 模式当前只支持 cn 语言");
        }
        if (command == null || command.length() > 160) {
            return Validation.invalid("动态唤醒命令不能为空且最长 160 个字符");
        }
        if (!CHINESE_COMMAND.matcher(command).matches()) {
            return Validation.invalid("动态命令必须是 3 到 8 个小写拼音音节，不能包含数字或特殊字符");
        }
        BigDecimal threshold = wakeThreshold == null ? DEFAULT_DYNAMIC_THRESHOLD : wakeThreshold;
        if (threshold.compareTo(MIN_THRESHOLD) < 0 || threshold.compareTo(MAX_THRESHOLD) > 0) {
            return Validation.invalid("动态唤醒阈值必须在 0.050 到 0.950 之间");
        }
        return Validation.active(mode, word, model, command, language,
                threshold.setScale(3, RoundingMode.HALF_UP), version);
    }

    public static Validation validateAtomicUpdate(String wakeMode, String wakeWord, String wakeModel,
            String wakeCommand, String wakeLanguage, BigDecimal wakeThreshold,
            Long wakeConfigVersion) {
        return validate(wakeMode, wakeWord, wakeModel, wakeCommand, wakeLanguage,
                wakeThreshold, wakeConfigVersion);
    }

    /** Backward-compatible atomic validation for older callers. */
    public static Validation validateAtomicUpdate(String wakeWord, String wakeModel) {
        if ((wakeWord == null) != (wakeModel == null)) {
            return Validation.invalid("更新角色唤醒配置时必须同时提交唤醒短语和模型");
        }
        return validate(wakeWord, wakeModel);
    }

    public static String normalize(String value) {
        String normalized = StringUtils.trimToNull(value);
        return normalized == null ? null : normalized;
    }

    private static String normalizeSpaces(String value) {
        String normalized = normalize(value);
        return normalized == null ? null : normalized.replaceAll("\\s+", " ");
    }

    private static boolean isUnsafeCodePoint(int codePoint) {
        return Character.isISOControl(codePoint)
                || codePoint == Character.LINE_SEPARATOR
                || codePoint == Character.PARAGRAPH_SEPARATOR;
    }

    public record Validation(boolean valid, boolean configured, String wakeMode,
            String wakeWord, String wakeModel, String wakeCommand, String wakeLanguage,
            BigDecimal wakeThreshold, Long wakeConfigVersion, String error) {
        private static Validation invalid(String error) {
            return new Validation(false, false, null, null, null, null, null, null, null, error);
        }

        private static Validation legacy() {
            return new Validation(true, false, null, null, null, null, null, null, null, null);
        }

        private static Validation active(String mode, String word, String model, String command,
                String language, BigDecimal threshold, long version) {
            return new Validation(true, true, mode.toLowerCase(Locale.ROOT), word, model,
                    command, language, threshold, version, null);
        }
    }
}
